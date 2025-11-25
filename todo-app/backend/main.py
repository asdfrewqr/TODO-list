from typing import List, Optional
from datetime import datetime
from fastapi import FastAPI, HTTPException, Depends, Query
from sqlmodel import Field, Session, SQLModel, create_engine, select
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager


# --- 1. 数据库模型设计 ---

class TodoBase(SQLModel):
    title: str = Field(index=True)
    description: Optional[str] = None
    is_completed: bool = False
    deadline: Optional[datetime] = Field(default=None)
    # 新增字段
    category: str = Field(default="Life")  # Work, Study, Life
    priority: int = Field(default=4)  # 1:重要紧急, 2:重要不紧急, 3:紧急不重要, 4:不紧急不重要


class Todo(TodoBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)


class TodoCreate(TodoBase):
    pass


class TodoUpdate(SQLModel):
    title: Optional[str] = None
    description: Optional[str] = None
    is_completed: Optional[bool] = None
    deadline: Optional[datetime] = None
    category: Optional[str] = None
    priority: Optional[int] = None


# --- 2. 数据库配置 ---
sqlite_file_name = "todo.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

engine = create_engine(sqlite_url, connect_args={"check_same_thread": False})


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session


# --- 3. FastAPI 应用初始化 ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield


app = FastAPI(lifespan=lifespan, title="Todo API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- 4. API 接口实现 ---

@app.get("/todos", response_model=List[Todo])
def read_todos(session: Session = Depends(get_session)):
    # 获取所有数据，排序逻辑交给前端处理更灵活
    statement = select(Todo)
    todos = session.exec(statement).all()
    return todos


@app.post("/todos", response_model=Todo)
def create_todo(todo_in: TodoCreate, session: Session = Depends(get_session)):
    todo = Todo.model_validate(todo_in)
    session.add(todo)
    session.commit()
    session.refresh(todo)
    return todo


# 通用更新接口 (用于修改分类、优先级、内容等)
@app.patch("/todos/{todo_id}", response_model=Todo)
def update_todo(todo_id: int, todo_update: TodoUpdate, session: Session = Depends(get_session)):
    todo = session.get(Todo, todo_id)
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")

    todo_data = todo_update.dict(exclude_unset=True)
    for key, value in todo_data.items():
        setattr(todo, key, value)

    session.add(todo)
    session.commit()
    session.refresh(todo)
    return todo


# 专门的 Toggle 接口 (保留以兼容旧逻辑，也可直接用上面的 update 替代)
@app.patch("/todos/{todo_id}/toggle", response_model=Todo)
def toggle_todo(todo_id: int, session: Session = Depends(get_session)):
    todo = session.get(Todo, todo_id)
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    todo.is_completed = not todo.is_completed
    session.add(todo)
    session.commit()
    session.refresh(todo)
    return todo


@app.delete("/todos/{todo_id}")
def delete_todo(todo_id: int, session: Session = Depends(get_session)):
    todo = session.get(Todo, todo_id)
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    session.delete(todo)
    session.commit()
    return {"ok": True}