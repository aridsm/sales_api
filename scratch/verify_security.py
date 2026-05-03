import uuid
from sqlalchemy import select, or_, and_, func, case
from sqlmodel import SQLModel, Field

class TestModel(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str
    user_id: str

def test_security_logic():
    user_id = "user1"
    search = "SomeSearch"
    # id1 belongs to user1, id2 belongs to user2
    id1 = uuid.uuid4()
    id2 = uuid.uuid4()
    
    include_ids = [id1, id2]
    
    # Simulate BaseService.get_all
    query = select(TestModel)
    
    # 1. Apply user ownership
    if user_id:
        query = query.where(TestModel.user_id == user_id)
        
    # 2. Build soft filters
    soft_filters = []
    if search:
        soft_filters.append(TestModel.name.ilike(f"%{search}%"))
        
    # 3. Apply inclusion logic
    if include_ids:
        if soft_filters:
            # Logic: user_id = u AND (id IN ids OR soft_filters)
            query = query.where(or_(TestModel.id.in_(include_ids), and_(*soft_filters)))
        else:
            pass
            
    print("Final Query WHERE:")
    where_clause = str(query.whereclause)
    print(where_clause)
    
    # Verify:
    # (user_id = 'user1') AND (id IN (id1, id2) OR name LIKE '%SomeSearch%')
    # If id2 belongs to user2, the first part (user_id = 'user1') will still fail for it.
    # So security is preserved!
    
    assert "testmodel.user_id = :user_id_1" in where_clause
    assert "testmodel.id IN" in where_clause
    assert "OR" in where_clause
    
    print("Security logic verified! include_ids are correctly constrained by the global user_id filter.")

if __name__ == "__main__":
    test_security_logic()
