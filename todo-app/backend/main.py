from typing import List, Optional
from fastapi import FastAPI, HTTPException, Depends, Query
from sqlmodel import Field, Session, SQLModel, create_engine, select
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

# --- 1. 数据库模型定义 (Database Model) ---
# 既是数据库表定义，也是 Pydantic 验证模型
class Todo(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(index=True)  # 必填
    description: Optional[str] = None
    is_completed: bool = Field(default=False)

# --- 2. 数据库配置 (Database Setup) ---
sqlite_file_name = "todo.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

# connect_args={"check_same_thread": False} 是 SQLite 必须的配置
engine = create_engine(sqlite_url, connect_args={"check_same_thread": False})

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

# 依赖注入：获取数据库会话
def get_session():
    with Session(engine) as session:
        yield session

# --- 3. FastAPI 应用初始化 ---
# lifespan 用于在应用启动时自动创建数据库表
@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield

app = FastAPI(lifespan=lifespan, title="Todo API", version="1.0.0")

# --- 4. CORS 配置 (解决前后端跨域问题) ---
# 允许前端 (http://localhost:5173) 访问后端
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 5. API 接口实现 (CRUD) ---

# 获取列表 (支持 ?completed=true/false 过滤)
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

# 创建任务
@app.post("/todos", response_model=Todo)
def create_todo(todo: Todo, session: Session = Depends(get_session)):
    session.add(todo)
    session.commit()
    session.refresh(todo)
    return todo

# 切换任务状态 (完成/未完成)
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

# 删除任务
@app.delete("/todos/{todo_id}")
def delete_todo(todo_id: int, session: Session = Depends(get_session)):
    todo = session.get(Todo, todo_id)
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    session.delete(todo)
    session.commit()
    return {"ok": True}