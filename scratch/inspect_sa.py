import uuid
from sqlalchemy import select, or_, and_, func
from sqlmodel import SQLModel, Field

class TestModel(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str
    user_id: str

def inspect_select():
    query = select(TestModel).where(TestModel.user_id == "1")
    print("Type of query:", type(query))
    
    # List all methods/attributes that look like they could manipulate where
    print("Attributes with 'where':", [a for a in dir(query) if "where" in a.lower()])
    print("Attributes with 'criteria':", [a for a in dir(query) if "criteria" in a.lower()])
    
    # Try the internal attribute mutation if it exists
    if hasattr(query, "_where_criteria"):
        print("Initial _where_criteria:", query._where_criteria)
        try:
            # Create a clone with different criteria
            # In SA 2.0, Select is often immutable but has methods to return new ones
            pass
        except Exception as e:
            print("Error:", e)

if __name__ == "__main__":
    inspect_select()
