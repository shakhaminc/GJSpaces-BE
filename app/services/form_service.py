import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.form import Form, FormField
from app.schemas.form import (
    FormCreate,
    FormFieldCreate,
    FormFieldReorderItem,
    FormFieldUpdate,
    FormUpdate,
)

logger = logging.getLogger(__name__)

PUNE_LOCATIONS = [
    "Singhgad Road", "Katraj", "Satara Road", "Kothrud", "Deccan", "Warje",
    "Bavdhan", "Pirangut", "Baner - Balewadi", "Mhalunge", "Hinjewadi Phase 1,2,3",
    "Wakad - Punawale", "Ravet - Mamurdi", "Pradhikaran", "Talegaon", "Kharadi",
    "Wagholi", "Vimannagar", "Dhanori", "Hadapsar", "NIBM", "Mundhawa",
    "Bund Garden", "Other"
]

FOS_NAMES = [
    "Pallavi Mam", "Trupti Mam", "Rupali Pawar", "Rohan Borude",
    "Shailendra Parmar", "Rohit Suryawanshi", "Rahul Talwalkar",
    "Abhishek Rathod", "Ganesh Jadhav", "Nishita"
]


# ==============================================================================
# Form Service Methods
# ==============================================================================

async def create_form(db: AsyncSession, form_in: FormCreate) -> Form:
    """Creates a new form definition."""
    dup_stmt = select(Form).where(
        (Form.form_title.ilike(form_in.form_title.strip()))
        & (Form.is_deleted == False)
    )
    existing = (await db.execute(dup_stmt)).scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Form with title '{form_in.form_title}' already exists."
        )

    form = Form(
        id=uuid.uuid4(),
        form_title=form_in.form_title.strip(),
        description=form_in.description,
        is_active=form_in.is_active,
    )
    db.add(form)
    await db.commit()
    return await get_form_by_id(db, form.id)


async def list_forms(db: AsyncSession, is_active: Optional[bool] = None) -> List[Dict[str, Any]]:
    """Retrieves all non-deleted forms with their respective active field counts."""
    stmt = (
        select(Form)
        .where(Form.is_deleted == False)
        .options(selectinload(Form.fields))
        .order_by(Form.created_at.desc())
    )
    if is_active is not None:
        stmt = stmt.where(Form.is_active == is_active)

    result = await db.execute(stmt)
    forms = result.scalars().all()

    response_items = []
    for f in forms:
        active_fields = [fld for fld in f.fields if not fld.is_deleted and fld.is_active]
        response_items.append({
            "id": f.id,
            "form_title": f.form_title,
            "description": f.description,
            "is_active": f.is_active,
            "field_count": len(active_fields),
            "created_at": f.created_at,
            "updated_at": f.updated_at,
        })
    return response_items


async def get_form_by_id(db: AsyncSession, form_id: uuid.UUID) -> Form:
    """Retrieves a form by its UUID along with all active, non-deleted fields ordered by display_order."""
    stmt = (
        select(Form)
        .where((Form.id == form_id) & (Form.is_deleted == False))
        .options(selectinload(Form.fields))
    )
    result = await db.execute(stmt)
    form = result.scalar_one_or_none()
    if not form:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Form with ID '{form_id}' was not found."
        )

    # Filter out soft-deleted fields and sort by display_order
    form.fields = sorted(
        [fld for fld in form.fields if not fld.is_deleted],
        key=lambda x: x.display_order
    )
    return form


async def update_form(db: AsyncSession, form_id: uuid.UUID, form_in: FormUpdate) -> Form:
    """Updates form metadata (title, description, is_active)."""
    form = await get_form_by_id(db, form_id)

    if form_in.form_title is not None and form_in.form_title.strip() != form.form_title:
        dup_stmt = select(Form).where(
            (Form.form_title.ilike(form_in.form_title.strip()))
            & (Form.id != form_id)
            & (Form.is_deleted == False)
        )
        existing = (await db.execute(dup_stmt)).scalar_one_or_none()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Another form with title '{form_in.form_title}' already exists."
            )
        form.form_title = form_in.form_title.strip()

    if form_in.description is not None:
        form.description = form_in.description
    if form_in.is_active is not None:
        form.is_active = form_in.is_active

    await db.commit()
    return await get_form_by_id(db, form_id)


async def delete_form(db: AsyncSession, form_id: uuid.UUID) -> bool:
    """Soft-deletes a form and all its associated fields."""
    form = await get_form_by_id(db, form_id)
    now = datetime.now(timezone.utc)

    form.is_deleted = True
    form.deleted_at = now

    for fld in form.fields:
        fld.is_deleted = True
        fld.deleted_at = now

    await db.commit()
    return True


# ==============================================================================
# Form Field Service Methods
# ==============================================================================

async def add_field_to_form(db: AsyncSession, form_id: uuid.UUID, field_in: FormFieldCreate) -> FormField:
    """Adds a new field to a form. If display_order is 0, appends to the end."""
    form = await get_form_by_id(db, form_id)

    # Determine display order if not explicitly set
    display_order = field_in.display_order
    if display_order == 0 and len(form.fields) > 0:
        max_order = max(fld.display_order for fld in form.fields)
        display_order = max_order + 1

    field = FormField(
        id=uuid.uuid4(),
        form_id=form.id,
        field_name=field_in.field_name.strip(),
        field_type=field_in.field_type.strip().lower(),
        is_required=field_in.is_required,
        display_order=display_order,
        options=field_in.options,
        is_active=field_in.is_active,
    )
    db.add(field)
    await db.commit()
    return await get_field_by_id(db, field.id)


async def get_field_by_id(db: AsyncSession, field_id: uuid.UUID) -> FormField:
    """Retrieves a single field by UUID."""
    stmt = select(FormField).where((FormField.id == field_id) & (FormField.is_deleted == False))
    result = await db.execute(stmt)
    field = result.scalar_one_or_none()
    if not field:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Field with ID '{field_id}' was not found."
        )
    return field


async def update_field(db: AsyncSession, field_id: uuid.UUID, field_in: FormFieldUpdate) -> FormField:
    """Updates field properties."""
    field = await get_field_by_id(db, field_id)

    if field_in.field_name is not None:
        field.field_name = field_in.field_name.strip()
    if field_in.field_type is not None:
        field.field_type = field_in.field_type.strip().lower()
    if field_in.is_required is not None:
        field.is_required = field_in.is_required
    if field_in.display_order is not None:
        field.display_order = field_in.display_order
    if field_in.options is not None:
        field.options = field_in.options
    if field_in.is_active is not None:
        field.is_active = field_in.is_active

    await db.commit()
    return await get_field_by_id(db, field_id)


async def delete_field(db: AsyncSession, field_id: uuid.UUID) -> bool:
    """Soft-deletes a field."""
    field = await get_field_by_id(db, field_id)
    field.is_deleted = True
    field.deleted_at = datetime.now(timezone.utc)
    await db.commit()
    return True


async def reorder_fields(
    db: AsyncSession,
    form_id: uuid.UUID,
    orders: List[FormFieldReorderItem]
) -> List[FormField]:
    """Updates display orders for a list of fields within a form in bulk."""
    form = await get_form_by_id(db, form_id)
    field_map = {fld.id: fld for fld in form.fields}

    for item in orders:
        if item.field_id in field_map:
            field_map[item.field_id].display_order = item.display_order

    await db.commit()

    stmt = (
        select(FormField)
        .where((FormField.form_id == form_id) & (FormField.is_deleted == False))
        .order_by(FormField.display_order)
    )
    res = await db.execute(stmt)
    return list(res.scalars().all())


# ==============================================================================
# Client 5 Forms Seeder
# ==============================================================================

async def seed_default_client_forms(db: AsyncSession) -> None:
    """Seeds the client's 5 reference Google Forms with their exact fields into the database."""
    default_forms = [
        # 1. Lead Format (26 Fields)
        {
            "form_title": "Lead Format",
            "description": "Client lead capture form for prospective property buyers",
            "fields": [
                {"field_name": "Customer Name", "field_type": "text", "is_required": True, "display_order": 1, "options": None},
                {"field_name": "Lead source", "field_type": "select", "is_required": False, "display_order": 2, "options": ["Self", "Company Data", "Rahul data", "Rohit data", "Ganesh Ref.", "Social media", "Pallavi mam ref.", "Bhavana mam ref."]},
                {"field_name": "Customer Contact No.", "field_type": "phone", "is_required": True, "display_order": 3, "options": None},
                {"field_name": "Configuration", "field_type": "select", "is_required": True, "display_order": 4, "options": ["1 BHK", "2 BHK", "3 BHK", "4 BHK", "Plotting", "Commercial (Shop,office space)", "Other"]},
                {"field_name": "Preferred Location", "field_type": "select", "is_required": True, "display_order": 5, "options": PUNE_LOCATIONS},
                {"field_name": "Tentative Budget", "field_type": "select", "is_required": True, "display_order": 6, "options": ["Below 50L", "50L - 80L", "80L - 1.2 Cr.", "1.2 Cr. - 2.5 Cr.", "2.5 Cr. - 5 Cr.", "5 Cr. Above"]},
                {"field_name": "How much funding is ready", "field_type": "text", "is_required": True, "display_order": 7, "options": None},
                {"field_name": "Carpet area", "field_type": "text", "is_required": False, "display_order": 8, "options": None},
                {"field_name": "Living in Own House or Rented", "field_type": "radio", "is_required": False, "display_order": 9, "options": ["Own", "Rented"]},
                {"field_name": "Since how long you are staying in current area (Months/Year)", "field_type": "text", "is_required": False, "display_order": 10, "options": None},
                {"field_name": "Possession Timeline", "field_type": "select", "is_required": True, "display_order": 11, "options": ["Ready", "Within a year", "Under Construction", "New launch", "Resale"]},
                {"field_name": "Purchasing Purpose", "field_type": "radio", "is_required": True, "display_order": 12, "options": ["For Investment", "For End use"]},
                {"field_name": "Occupation", "field_type": "select", "is_required": False, "display_order": 13, "options": ["Salaried", "Professional", "Business", "Self employed", "Retired", "Other"]},
                {"field_name": "Company Name", "field_type": "text", "is_required": False, "display_order": 14, "options": None},
                {"field_name": "Company location", "field_type": "text", "is_required": False, "display_order": 15, "options": None},
                {"field_name": "Designation", "field_type": "text", "is_required": False, "display_order": 16, "options": None},
                {"field_name": "Married", "field_type": "radio", "is_required": False, "display_order": 17, "options": ["Yes", "No"]},
                {"field_name": "Kids", "field_type": "radio", "is_required": False, "display_order": 18, "options": ["Yes", "No"]},
                {"field_name": "School Details", "field_type": "text", "is_required": False, "display_order": 19, "options": None},
                {"field_name": "Want to take a loan?", "field_type": "boolean", "is_required": True, "display_order": 20, "options": ["Yes", "No"]},
                {"field_name": "Tentitive loan amount required.", "field_type": "text", "is_required": False, "display_order": 21, "options": None},
                {"field_name": "Preferred Bank Name for loan", "field_type": "text", "is_required": False, "display_order": 22, "options": None},
                {"field_name": "Family Income (in Lakh)", "field_type": "text", "is_required": False, "display_order": 23, "options": None},
                {"field_name": "Which company car you are using?", "field_type": "text", "is_required": False, "display_order": 24, "options": None},
                {"field_name": "Next Call date", "field_type": "date", "is_required": True, "display_order": 25, "options": None},
                {"field_name": "Comment", "field_type": "textarea", "is_required": False, "display_order": 26, "options": None},
            ]
        },
        # 2. Project Form (29 Fields)
        {
            "form_title": "Project Form",
            "description": "Residential project details and developer registration form",
            "fields": [
                {"field_name": "FOS Name", "field_type": "select", "is_required": True, "display_order": 1, "options": ["Pallavi Mam", "Trupti Mam", "Rupali Pawar", "Rohan Borude", "Shailendra Parmar", "Rohit Suryawanshi", "Rahul Talwalkar", "Abhishek Rathod", "Ganesh Jadhav"]},
                {"field_name": "Project Name", "field_type": "text", "is_required": True, "display_order": 2, "options": None},
                {"field_name": "Builder Name", "field_type": "text", "is_required": False, "display_order": 3, "options": None},
                {"field_name": "RERA Number", "field_type": "text", "is_required": True, "display_order": 4, "options": None},
                {"field_name": "Preferred Location", "field_type": "select", "is_required": True, "display_order": 5, "options": PUNE_LOCATIONS},
                {"field_name": "Sub Location", "field_type": "text", "is_required": True, "display_order": 6, "options": None},
                {"field_name": "Total Land Parcel", "field_type": "text", "is_required": True, "display_order": 7, "options": None},
                {"field_name": "Total Wings", "field_type": "number", "is_required": True, "display_order": 8, "options": None},
                {"field_name": "Total Wings Launched", "field_type": "number", "is_required": False, "display_order": 9, "options": None},
                {"field_name": "Total Stories", "field_type": "number", "is_required": True, "display_order": 10, "options": None},
                {"field_name": "Flats Per Floor", "field_type": "number", "is_required": True, "display_order": 11, "options": None},
                {"field_name": "Total Units", "field_type": "number", "is_required": True, "display_order": 12, "options": None},
                {"field_name": "2 BHK Carpet Area", "field_type": "textarea", "is_required": False, "display_order": 13, "options": None},
                {"field_name": "3 BHK Carpet Area", "field_type": "text", "is_required": False, "display_order": 14, "options": None},
                {"field_name": "4 BHK Carpet Area", "field_type": "text", "is_required": False, "display_order": 15, "options": None},
                {"field_name": "Other Carpet Area", "field_type": "text", "is_required": False, "display_order": 16, "options": None},
                {"field_name": "2 BHK Costing", "field_type": "text", "is_required": True, "display_order": 17, "options": None},
                {"field_name": "3 BHK Costing", "field_type": "text", "is_required": True, "display_order": 18, "options": None},
                {"field_name": "4 BHK Costing", "field_type": "text", "is_required": False, "display_order": 19, "options": None},
                {"field_name": "Other Costing", "field_type": "text", "is_required": False, "display_order": 20, "options": None},
                {"field_name": "Amenities", "field_type": "textarea", "is_required": False, "display_order": 21, "options": None},
                {"field_name": "Unique Selling Points", "field_type": "text", "is_required": False, "display_order": 22, "options": None},
                {"field_name": "Other Projects of Same Builder", "field_type": "text", "is_required": True, "display_order": 23, "options": None},
                {"field_name": "RERA Possession & Builder Commitment", "field_type": "text", "is_required": True, "display_order": 24, "options": None},
                {"field_name": "Project Marketed by", "field_type": "select", "is_required": True, "display_order": 25, "options": ["Builder", "Sole selling company / Mandate Firm"]},
                {"field_name": "Sourcing Manager Name & Number", "field_type": "text", "is_required": True, "display_order": 26, "options": None},
                {"field_name": "Site Head Name & Number", "field_type": "text", "is_required": False, "display_order": 27, "options": None},
                {"field_name": "CP Payout (starting in Percentage)", "field_type": "text", "is_required": True, "display_order": 28, "options": None},
                {"field_name": "Tagging Period (In Days / Months)", "field_type": "text", "is_required": True, "display_order": 29, "options": None},
            ]
        },
        # 3. Plotting Form (12 Fields)
        {
            "form_title": "Plotting Form",
            "description": "Land and plotting project registration form",
            "fields": [
                {"field_name": "FOS Name", "field_type": "select", "is_required": False, "display_order": 1, "options": FOS_NAMES},
                {"field_name": "Plotting Type", "field_type": "select", "is_required": False, "display_order": 2, "options": ["Agriculture", "R - Zone", "NA", "Gunthewari"]},
                {"field_name": "Preferred Location", "field_type": "select", "is_required": True, "display_order": 3, "options": PUNE_LOCATIONS},
                {"field_name": "Total No. of Plots", "field_type": "number", "is_required": False, "display_order": 4, "options": None},
                {"field_name": "Min. Plot Sizes", "field_type": "text", "is_required": False, "display_order": 5, "options": None},
                {"field_name": "Max. Plot Size", "field_type": "text", "is_required": False, "display_order": 6, "options": None},
                {"field_name": "Min. Costing", "field_type": "text", "is_required": False, "display_order": 7, "options": None},
                {"field_name": "Max. Costing", "field_type": "text", "is_required": False, "display_order": 8, "options": None},
                {"field_name": "How much FSI per Plot", "field_type": "text", "is_required": False, "display_order": 9, "options": None},
                {"field_name": "Possession", "field_type": "text", "is_required": False, "display_order": 10, "options": None},
                {"field_name": "Builder any other Projects", "field_type": "text", "is_required": False, "display_order": 11, "options": None},
                {"field_name": "Is Investor deal available", "field_type": "select", "is_required": False, "display_order": 12, "options": ["Yes", "No", "Depends upon Payment schedule"]},
            ]
        },
        # 4. Commercial Project Form (21 Fields)
        {
            "form_title": "Commercial Project Form",
            "description": "Commercial shop, office space, and studio project registration form",
            "fields": [
                {"field_name": "FOS Name", "field_type": "select", "is_required": False, "display_order": 1, "options": FOS_NAMES},
                {"field_name": "Project Name", "field_type": "text", "is_required": False, "display_order": 2, "options": None},
                {"field_name": "Builder Name", "field_type": "text", "is_required": False, "display_order": 3, "options": None},
                {"field_name": "Commercial Type", "field_type": "select", "is_required": False, "display_order": 4, "options": ["Shop", "Office", "Studio"]},
                {"field_name": "Preferred Location", "field_type": "select", "is_required": True, "display_order": 5, "options": PUNE_LOCATIONS},
                {"field_name": "Location Landmark", "field_type": "text", "is_required": False, "display_order": 6, "options": None},
                {"field_name": "Min. Carpet Area of Office", "field_type": "text", "is_required": False, "display_order": 7, "options": None},
                {"field_name": "Max.Carpet area of office", "field_type": "text", "is_required": False, "display_order": 8, "options": None},
                {"field_name": "Min.Carpet Area of Shop", "field_type": "text", "is_required": False, "display_order": 9, "options": None},
                {"field_name": "Max. Carpet Area of Shops", "field_type": "text", "is_required": False, "display_order": 10, "options": None},
                {"field_name": "Min.carpet of Studio", "field_type": "text", "is_required": False, "display_order": 11, "options": None},
                {"field_name": "Max. Carpet of Studio", "field_type": "text", "is_required": False, "display_order": 12, "options": None},
                {"field_name": "Min. Cost of Office", "field_type": "text", "is_required": False, "display_order": 13, "options": None},
                {"field_name": "Max Cost of office", "field_type": "text", "is_required": False, "display_order": 14, "options": None},
                {"field_name": "Min Cost of shop", "field_type": "text", "is_required": False, "display_order": 15, "options": None},
                {"field_name": "Max cost of shop", "field_type": "text", "is_required": False, "display_order": 16, "options": None},
                {"field_name": "Min. Cost of Studio", "field_type": "text", "is_required": False, "display_order": 17, "options": None},
                {"field_name": "Max. Cost of Studio", "field_type": "text", "is_required": False, "display_order": 18, "options": None},
                {"field_name": "Possession", "field_type": "text", "is_required": False, "display_order": 19, "options": None},
                {"field_name": "Tentitive ROI", "field_type": "select", "is_required": False, "display_order": 20, "options": ["Below 6.5%", "Above 6.5 %"]},
                {"field_name": "Any Investor Deal Available", "field_type": "select", "is_required": False, "display_order": 21, "options": ["Yes", "No", "Depend upon Payment Schedule"]},
            ]
        },
        # 5. Loan Format (9 Fields)
        {
            "form_title": "Loan Format",
            "description": "Loan lead capture format for home, vehicle, and personal loans",
            "fields": [
                {"field_name": "Lead Source", "field_type": "select", "is_required": True, "display_order": 1, "options": ["Ganesh Jadhav", "Rahul", "Company Data", "Rohit Data", "Siddhant", "Self", "Social Media"]},
                {"field_name": "Executive Name", "field_type": "text", "is_required": True, "display_order": 2, "options": None},
                {"field_name": "Customer Name", "field_type": "text", "is_required": True, "display_order": 3, "options": None},
                {"field_name": "Customer Contact No.", "field_type": "phone", "is_required": True, "display_order": 4, "options": None},
                {"field_name": "Employment Status", "field_type": "select", "is_required": False, "display_order": 5, "options": ["Employed", "Unemployed", "Retired", "Self Employed (Business)"]},
                {"field_name": "Loan Type", "field_type": "select", "is_required": True, "display_order": 6, "options": ["Home Loan", "Vehicle Loan", "Personal Loan", "Mortgage Loan", "Educational Loan", "Other"]},
                {"field_name": "Tentative Loan amount required", "field_type": "text", "is_required": True, "display_order": 7, "options": None},
                {"field_name": "Next Call date", "field_type": "date", "is_required": False, "display_order": 8, "options": None},
                {"field_name": "Comment", "field_type": "textarea", "is_required": False, "display_order": 9, "options": None},
            ]
        }
    ]

    for item in default_forms:
        stmt = select(Form).where(
            (Form.form_title.ilike(item["form_title"].strip()))
            & (Form.is_deleted == False)
        )
        existing = (await db.execute(stmt)).scalar_one_or_none()
        if existing:
            continue

        form = Form(
            id=uuid.uuid4(),
            form_title=item["form_title"],
            description=item["description"],
            is_active=True,
        )
        db.add(form)
        await db.flush()

        for fld in item["fields"]:
            field_obj = FormField(
                id=uuid.uuid4(),
                form_id=form.id,
                field_name=fld["field_name"],
                field_type=fld["field_type"],
                is_required=fld["is_required"],
                display_order=fld["display_order"],
                options=fld["options"],
                is_active=True,
            )
            db.add(field_obj)

        logger.info(f"Seeded form '{item['form_title']}' with {len(item['fields'])} fields.")

    await db.commit()
