from typing import List, Optional
from datetime import datetime
from fastapi import FastAPI, HTTPException, Depends, Query
from sqlmodel import Field, Session, SQLModel, create_engine, select
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

# --- 1. 数据库模型设计 (Model Design) ---

# 基础模型：定义共有字段
# Pydantic 会利用这个模型将前端传来的 ISO 字符串自动转换为 Python datetime 对象
class TodoBase(SQLModel):
    title: str = Field(index=True)
    description: Optional[str] = None
    is_completed: bool = False
    deadline: Optional[datetime] = Field(default=None)

# 数据库表模型：继承基础模型，并添加 ID 主键
class Todo(TodoBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

# 创建请求模型：用于接收前端创建请求 (与 Base 一致，但语义不同)
class TodoCreate(TodoBase):
    pass

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

app = FastAPI(lifespan=lifespan, title="Todo API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 4. API 接口实现 ---

@app.get("/todos", response_model=List[Todo])
def read_todos(
    completed: Optional[bool] = None,
    session: Session = Depends(get_session)
):
    statement = select(Todo)
    if completed is not None:
        statement = statement.where(Todo.is_completed == completed)
    todos = session.exec(statement).all()
    return todos

# 关键修改：接收 TodoCreate，转换为Todo
@app.post("/todos", response_model=Todo)
def create_todo(todo_in: TodoCreate, session: Session = Depends(get_session)):
    # model_validate 会自动处理类型转换 (从 TodoCreate 里的 datetime 转换到Todo 表模型)
    todo = Todo.model_validate(todo_in)
    session.add(todo)
    session.commit()
    session.refresh(todo)
    return todo

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