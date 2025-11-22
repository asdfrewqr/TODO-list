<script setup>
import { ref, onMounted, computed } from 'vue'
import axios from 'axios'

// --- 状态管理 ---
const todos = ref([])
const newTodoTitle = ref('')
const newTodoContent = ref('') // 新增：用于存储任务内容/详情
const loading = ref(false)
const filter = ref('all')

// 后端 API 地址 (请确保端口与后端启动端口一致)
const API_URL = 'http://127.0.0.1:8000/todos'

// --- API 交互方法 ---

// 获取数据 (已改为 function 格式)
async function fetchTodos() {
  loading.value = true
  try {
    const { data } = await axios.get(API_URL)
    todos.value = data
  } catch (error) {
    console.error('Failed to fetch todos', error)
    // 使用 window.alert 防止编译环境报错
    window.alert('无法连接到服务器，请确认后端已启动')
  } finally {
    loading.value = false
  }
}

// 添加任务 (已改为 function 格式)
async function addTodo() {
  const title = newTodoTitle.value.trim()
  const content = newTodoContent.value.trim() // 获取内容

  if (!title) {
    window.alert('任务标题不能为空') // 标题仍为必填项
    return
  }

  try {
    const { data } = await axios.post(API_URL, {
      title: title,
      description: content || null, // 如果内容为空，发送 null
      is_completed: false
    })
    todos.value.push(data)
    newTodoTitle.value = ''
    newTodoContent.value = '' // 清空内容输入框
  } catch (error) {
    console.error('Add failed', error)
    window.alert('添加失败')
  }
}

// 切换完成状态 (已改为 function 格式)
async function toggleTodo(todo) {
  // 乐观更新 (Optimistic Update): 先改 UI，体验更快
  const originalState = todo.is_completed
  todo.is_completed = !todo.is_completed

  try {
    await axios.patch(`${API_URL}/${todo.id}/toggle`)
  } catch (error) {
    // 如果失败，回滚状态
    todo.is_completed = originalState
    window.alert('操作失败')
  }
}

// 删除任务 (已改为 function 格式)
async function deleteTodo(id) {
  if (!window.confirm('确定要删除吗？')) return

  try {
    await axios.delete(`${API_URL}/${id}`)
    todos.value = todos.value.filter(t => t.id !== id)
  } catch (error) {
    console.error('Delete failed', error)
  }
}

// --- 计算属性 (前端过滤) ---
const filteredTodos = computed(() => {
  if (filter.value === 'active') return todos.value.filter(t => !t.is_completed)
  if (filter.value === 'completed') return todos.value.filter(t => t.is_completed)
  return todos.value
})

// 页面加载时自动获取数据
onMounted(fetchTodos)
</script>

<template>
  <div class="container">
    <header>
      <h1>📝 Todo List</h1>
      <p class="subtitle">FastAPI + Vue 3 + SQLite</p>
    </header>

    <!-- 输入区域 (已修改：包含标题和内容输入) -->
    <div class="input-form">
      <input
        v-model="newTodoTitle"
        placeholder="输入任务标题 (必填)..."
        :disabled="loading"
        class="title-input"
      />
      <textarea
        v-model="newTodoContent"
        placeholder="输入任务详情/内容 (可选)..."
        :disabled="loading"
        class="content-input"
      ></textarea>
      <button @click="addTodo" :disabled="!newTodoTitle.trim() || loading">Add Task</button>
    </div>

    <!-- 过滤器 -->
    <div class="filters">
      <button :class="{ active: filter === 'all' }" @click="filter = 'all'">All</button>
      <button :class="{ active: filter === 'active' }" @click="filter = 'active'">Active</button>
      <button :class="{ active: filter === 'completed' }" @click="filter = 'completed'">Completed</button>
    </div>

    <!-- 列表区域 -->
    <div v-if="loading" class="loading">Loading tasks...</div>

    <ul v-else class="todo-list">
      <li v-for="todo in filteredTodos" :key="todo.id" :class="{ completed: todo.is_completed }">
        <label class="todo-content">
          <input
            type="checkbox"
            :checked="todo.is_completed"
            @change="toggleTodo(todo)"
          >
          <!-- 显示标题和内容 -->
          <div class="text-group">
            <span class="todo-title">{{ todo.title }}</span>
            <p v-if="todo.description" class="todo-description">{{ todo.description }}</p>
          </div>
        </label>
        <button class="delete-btn" @click="deleteTodo(todo.id)">Delete</button>
      </li>

      <li v-if="filteredTodos.length === 0" class="empty-state">
        No tasks found.
      </li>
    </ul>
  </div>
</template>

<style scoped>
/* 简单的样式，模拟 Notion/现代化 风格 */
.container { max-width: 600px; margin: 0 auto; padding: 2rem; font-family: -apple-system, BlinkMacSystemFont, sans-serif; }
header { text-align: center; margin-bottom: 2rem; }
h1 { margin: 0; color: #333; }
.subtitle { color: #666; font-size: 0.9rem; }

/* 新的表单布局 */
.input-form {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 1.5rem;
  padding: 15px;
  border: 1px solid #ddd;
  border-radius: 8px;
  background-color: #f9f9f9;
}

.title-input {
  padding: 10px; border: 1px solid #ddd; border-radius: 6px; font-size: 1rem; outline: none; transition: border-color 0.2s;
}
.title-input:focus { border-color: #0070f3; }

.content-input {
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 0.9rem;
  min-height: 80px;
  resize: vertical;
  outline: none;
  transition: border-color 0.2s;
}
.content-input:focus { border-color: #0070f3; }

/* 按钮位于底部，全宽 */
.input-form button {
    width: 100%;
    margin-top: 5px;
    padding: 10px 16px;
    background: #0070f3;
    color: white;
    border: none;
    border-radius: 6px;
    cursor: pointer;
    font-weight: 600;
    transition: opacity 0.2s;
}
.input-form button:hover { opacity: 0.9; }
.input-form button:disabled { background: #ccc; cursor: not-allowed; }


/* 列表和内容显示更新 */
.todo-list { list-style: none; padding: 0; border: 1px solid #eaeaea; border-radius: 8px; overflow: hidden; }
.todo-list li { display: flex; justify-content: space-between; align-items: center; padding: 12px 16px; border-bottom: 1px solid #eaeaea; background: white; }
.todo-list li:last-child { border-bottom: none; }

.todo-content {
  display: flex;
  align-items: flex-start; /* 确保复选框和内容组顶部对齐 */
  gap: 10px;
  cursor: pointer;
  flex: 1;
}
.text-group {
    display: flex;
    flex-direction: column;
    flex: 1;
}
.todo-title {
    font-weight: 500;
    line-height: 1.2;
}
.todo-description {
    margin: 4px 0 0 0;
    font-size: 0.85rem;
    color: #888;
    line-height: 1.4;
    white-space: pre-wrap; /* 保持输入框内的换行和格式 */
}

/* 完成状态样式 */
.completed .todo-title {
    text-decoration: line-through;
    color: #aaa;
}
.completed .todo-description {
    text-decoration: line-through;
    color: #ccc;
}

/* 过滤器按钮和删除按钮保持不变 */
.filters { display: flex; gap: 10px; margin-bottom: 1rem; justify-content: center; }
.filters button { background: transparent; color: #666; border: 1px solid transparent; }
.filters button.active { background: #e6f7ff; color: #0070f3; }

button.delete-btn { background: transparent; color: #ff4d4f; font-size: 0.8rem; padding: 4px 8px; border: 1px solid transparent; }
button.delete-btn:hover { background: #fff1f0; border-color: #ffa39e; }

.empty-state { padding: 20px; text-align: center; color: #999; justify-content: center; }
.loading { text-align: center; color: #666; margin: 20px 0; }
</style>