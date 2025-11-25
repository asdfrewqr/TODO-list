<script setup>
import { ref, onMounted, computed } from 'vue';
import axios from 'axios';

// --- 状态管理 ---
const todos = ref([]);
const newTodoTitle = ref('');
const newTodoContent = ref('');
const newTodoDeadline = ref('');
const loading = ref(false);
const filter = ref('all');
const API_URL = 'http://127.0.0.1:8000/todos';

// --- 核心逻辑 (使用最稳健的写法) ---

const fetchTodos = function() {
  loading.value = true;
  axios.get(API_URL)
    .then(function(res) {
      todos.value = res.data;
    })
    .catch(function(err) {
      console.error(err);
    })
    .finally(function() {
      loading.value = false;
    });
};

const addTodo = function() {
  if (!newTodoTitle.value.trim()) return;

  let deadlineISO = null;
  if (newTodoDeadline.value) {
    deadlineISO = new Date(newTodoDeadline.value).toISOString();
  }

  axios.post(API_URL, {
    title: newTodoTitle.value,
    description: newTodoContent.value || null,
    is_completed: false,
    deadline: deadlineISO
  })
  .then(function(res) {
    todos.value.push(res.data);
    newTodoTitle.value = '';
    newTodoContent.value = '';
    newTodoDeadline.value = '';
  })
  .catch(function(err) {
    if (typeof window !== 'undefined') alert('Error adding task');
  });
};

const toggleTodo = function(todo) {
  const original = todo.is_completed;
  todo.is_completed = !todo.is_completed;

  axios.patch(API_URL + '/' + todo.id + '/toggle')
    .catch(function(err) {
      todo.is_completed = original;
    });
};

const deleteTodo = function(id) {
  if (typeof window !== 'undefined' && !confirm('Delete this task?')) return;

  axios.delete(API_URL + '/' + id)
    .then(function() {
      todos.value = todos.value.filter(function(t) { return t.id !== id; });
    })
    .catch(function(err) {
      console.error(err);
    });
};

// --- 辅助函数 ---

const getCountdown = function(deadlineStr) {
  if (!deadlineStr) return null;

  let clean = deadlineStr;
  if (clean.indexOf('Z') === -1 && clean.indexOf('+') === -1) clean += 'Z';

  const now = new Date();
  const target = new Date(clean);
  const diff = target - now;

  if (diff < 0) return { overdue: true, text: 'TIMEOUT' };

  const d = Math.floor(diff / (1000 * 60 * 60 * 24));
  const h = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
  const m = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));

  let t = '';
  if (d > 0) t += d + 'd ';
  t += h + 'h ' + m + 'm';

  return { overdue: false, text: t };
};

// --- 计算属性 ---

const completedCount = computed(function() {
  return todos.value.filter(function(t) { return t.is_completed; }).length;
});
const pendingCount = computed(function() {
  return todos.value.filter(function(t) { return !t.is_completed; }).length;
});
const totalCount = computed(function() {
  return todos.value.length;
});

const filteredTodos = computed(function() {
  if (filter.value === 'active') return todos.value.filter(function(t) { return !t.is_completed; });
  if (filter.value === 'completed') return todos.value.filter(function(t) { return t.is_completed; });
  return todos.value;
});

// --- 交互效果 ---

const handleCardMove = function(e) {
  const card = e.currentTarget;
  const rect = card.getBoundingClientRect();
  const x = e.clientX - rect.left;
  const y = e.clientY - rect.top;

  const rotateY = (x / rect.width - 0.5) * 5;
  const rotateX = (y / rect.height - 0.5) * -5;

  card.style.transform = 'perspective(1000px) rotateX(' + rotateX + 'deg) rotateY(' + rotateY + 'deg) scale(1.01)';
  card.style.zIndex = '10';
};

const handleCardLeave = function(e) {
  const card = e.currentTarget;
  card.style.transform = 'perspective(1000px) rotateX(0) rotateY(0) scale(1)';
  card.style.zIndex = '1';
};

onMounted(function() {
  fetchTodos();
});
</script>

<template>
  <div class="app-container">
    <!-- 背景 -->
    <div class="bg-gradient"></div>

    <div class="layout-grid">
      <!-- 侧边栏 -->
      <aside class="sidebar">
        <div class="logo">
          <i class="fab fa-react fa-2x spin"></i>
          <span>BlueOS</span>
        </div>

        <nav class="nav-menu">
          <div class="nav-item" :class="{ active: filter === 'all' }" @click="filter = 'all'">
            <i class="fas fa-layer-group"></i>
            <span>Overview</span>
          </div>
          <div class="nav-item" :class="{ active: filter === 'active' }" @click="filter = 'active'">
            <i class="fas fa-bolt"></i>
            <span>Active</span>
          </div>
          <div class="nav-item" :class="{ active: filter === 'completed' }" @click="filter = 'completed'">
            <i class="fas fa-check-circle"></i>
            <span>Done</span>
          </div>
        </nav>

        <div class="user-profile">
          <div class="avatar"></div>
          <div class="user-details">
            <span class="name">Admin</span>
            <span class="role">System Level</span>
          </div>
        </div>
      </aside>

      <!-- 主内容区 -->
      <main class="main-content">
        <header class="top-bar">
          <h1>Task Dashboard</h1>
          <div class="system-status">
            <span class="status-dot"></span>
            SYSTEM ONLINE
          </div>
        </header>

        <!-- 统计卡片 -->
        <div class="stats-row">
          <div class="stat-card blue" @mousemove="handleCardMove" @mouseleave="handleCardLeave">
            <div class="icon-box"><i class="fas fa-tasks"></i></div>
            <div class="stat-info">
              <h3>{{ totalCount }}</h3>
              <p>Total Tasks</p>
            </div>
          </div>
          <div class="stat-card cyan" @mousemove="handleCardMove" @mouseleave="handleCardLeave">
            <div class="icon-box"><i class="fas fa-clock"></i></div>
            <div class="stat-info">
              <h3>{{ pendingCount }}</h3>
              <p>Pending</p>
            </div>
          </div>
          <div class="stat-card indigo" @mousemove="handleCardMove" @mouseleave="handleCardLeave">
            <div class="icon-box"><i class="fas fa-check"></i></div>
            <div class="stat-info">
              <h3>{{ completedCount }}</h3>
              <p>Completed</p>
            </div>
          </div>
        </div>

        <!-- 输入模块 (纵向排列) -->
        <div class="input-module glass-panel">
          <div class="module-title"><i class="fas fa-plus-circle"></i> Create New Task</div>

          <div class="input-stack">
            <div class="input-group">
              <label>Task Title</label>
              <input v-model="newTodoTitle" placeholder="What needs to be done?" class="glass-input" @keyup.enter="addTodo">
            </div>

            <div class="input-group">
              <label>Description</label>
              <input v-model="newTodoContent" placeholder="Add details..." class="glass-input" @keyup.enter="addTodo">
            </div>

            <div class="input-group">
              <label>Deadline</label>
              <input type="datetime-local" v-model="newTodoDeadline" class="glass-input date-picker">
            </div>

            <button class="action-btn" @click="addTodo">
              Create Task <i class="fas fa-arrow-right"></i>
            </button>
          </div>
        </div>

        <!-- 任务列表 -->
        <div class="todo-list">
          <div v-if="loading" class="state-text">Loading data...</div>
          <div v-else-if="filteredTodos.length === 0" class="state-text">No tasks found.</div>

          <div
            v-for="todo in filteredTodos"
            :key="todo.id"
            class="todo-item glass-panel"
            :class="{ 'is-done': todo.is_completed }"
            @mousemove="handleCardMove"
            @mouseleave="handleCardLeave"
          >
            <div class="item-header">
              <span class="id-tag">#{{ todo.id }}</span>
              <button class="del-btn" @click.stop="deleteTodo(todo.id)"><i class="fas fa-times"></i></button>
            </div>

            <div class="item-body" @click="toggleTodo(todo)">
              <h4>{{ todo.title }}</h4>
              <p>{{ todo.description || 'No description' }}</p>
            </div>

            <div class="item-footer">
              <div class="status-badge" :class="todo.is_completed ? 'done' : 'active'">
                {{ todo.is_completed ? 'COMPLETED' : 'IN PROGRESS' }}
              </div>

              <div v-if="todo.deadline && !todo.is_completed"
                   class="time-badge"
                   :class="{ 'warn': getCountdown(todo.deadline).overdue }">
                <i class="far fa-clock"></i> {{ getCountdown(todo.deadline).text }}
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  </div>
</template>

<style>
/* 全局重置 */
* { margin: 0; padding: 0; box-sizing: border-box; }
html, body { width: 100%; height: 100%; overflow: hidden; font-family: 'Segoe UI', sans-serif; }
</style>

<style scoped>
@import url("https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css");

:root {
  --primary: #00f2ff;
  --secondary: #0066ff;
  --text: #ffffff;
  --glass-bg: rgba(255, 255, 255, 0.1);
  --glass-border: rgba(255, 255, 255, 0.2);
  --panel-bg: rgba(10, 20, 40, 0.7);
}

.app-container {
  width: 100%;
  height: 100%;
  background-color: #050a14; /* 深蓝黑底色 */
  color: white;
  position: fixed;
  top: 0; left: 0;
}

/* 动态渐变背景 */
.bg-gradient {
  position: absolute;
  top: -50%; left: -50%;
  width: 200%; height: 200%;
  background: radial-gradient(circle at 50% 50%, rgba(0, 102, 255, 0.15), transparent 60%),
              radial-gradient(circle at 80% 20%, rgba(0, 242, 255, 0.1), transparent 40%);
  z-index: 0;
  animation: rotate 60s linear infinite;
}
@keyframes rotate { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }

.layout-grid {
  position: relative; z-index: 1;
  display: flex;
  width: 100%; height: 100%;
}

/* --- 侧边栏 --- */
.sidebar {
  width: 260px;
  height: 100%;
  background: rgba(10, 25, 50, 0.85); /* 深蓝半透明 */
  backdrop-filter: blur(20px);
  border-right: 1px solid rgba(255, 255, 255, 0.1);
  display: flex; flex-direction: column;
  padding: 20px;
  flex-shrink: 0;
}

.logo {
  display: flex; align-items: center; gap: 10px;
  font-size: 24px; font-weight: bold; color: #00f2ff;
  margin-bottom: 40px; padding-left: 10px;
}
.spin { animation: spin 10s linear infinite; }
@keyframes spin { 100% { transform: rotate(360deg); } }

.nav-menu { display: flex; flex-direction: column; gap: 8px; }
.nav-item {
  display: flex; align-items: center; gap: 15px;
  padding: 12px 15px;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.3s;
  color: #a0b0c0;
  font-weight: 500;
}
.nav-item:hover { background: rgba(255, 255, 255, 0.05); color: white; }
.nav-item.active {
  background: linear-gradient(90deg, rgba(0, 102, 255, 0.2), transparent);
  border-left: 3px solid #00f2ff;
  color: #00f2ff;
}

.user-profile {
  margin-top: auto;
  display: flex; align-items: center; gap: 12px;
  padding: 15px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 12px;
}
.avatar { width: 36px; height: 36px; background: #0066ff; border-radius: 50%; }
.user-details { display: flex; flex-direction: column; }
.name { font-size: 14px; font-weight: bold; }
.role { font-size: 12px; color: #00f2ff; }

/* --- 主内容区 --- */
.main-content {
  flex: 1;
  padding: 30px 40px;
  overflow-y: auto;
  display: flex; flex-direction: column; gap: 30px;
}

.top-bar {
  display: flex; justify-content: space-between; align-items: center;
}
h1 { font-size: 28px; font-weight: 600; color: #e0f0ff; }
.system-status {
  display: flex; align-items: center; gap: 8px;
  font-size: 12px; color: #00f2ff; letter-spacing: 1px; font-weight: bold;
}
.status-dot { width: 8px; height: 8px; background: #00f2ff; border-radius: 50%; box-shadow: 0 0 10px #00f2ff; }

/* --- 统计卡片 (淡蓝色系) --- */
.stats-row {
  display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 20px;
}
.stat-card {
  padding: 20px; border-radius: 16px;
  display: flex; align-items: center; gap: 20px;
  background: rgba(20, 40, 70, 0.6); /* 淡蓝底 */
  border: 1px solid rgba(100, 200, 255, 0.2);
  backdrop-filter: blur(10px);
  transition: transform 0.2s;
}
.icon-box {
  width: 50px; height: 50px; border-radius: 12px;
  display: flex; align-items: center; justify-content: center;
  font-size: 20px; background: rgba(255, 255, 255, 0.1);
}
.blue .icon-box { color: #00f2ff; box-shadow: 0 0 15px rgba(0, 242, 255, 0.2); }
.cyan .icon-box { color: #00aaff; box-shadow: 0 0 15px rgba(0, 170, 255, 0.2); }
.indigo .icon-box { color: #6699ff; box-shadow: 0 0 15px rgba(102, 153, 255, 0.2); }

.stat-info h3 { font-size: 24px; font-weight: bold; }
.stat-info p { font-size: 13px; color: #a0c0ff; }

/* --- 输入模块 (纵向堆叠) --- */
.glass-panel {
  background: rgba(20, 30, 50, 0.7);
  border: 1px solid rgba(100, 200, 255, 0.2);
  backdrop-filter: blur(10px);
  border-radius: 16px;
}

.input-module { padding: 25px; }
.module-title {
  color: #00f2ff; font-weight: bold; margin-bottom: 20px;
  display: flex; align-items: center; gap: 8px;
}

.input-stack { display: flex; flex-direction: column; gap: 15px; }
.input-group { display: flex; flex-direction: column; gap: 6px; }
.input-group label { font-size: 12px; color: #80a0c0; font-weight: 600; }

.glass-input {
  background: rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 8px;
  padding: 12px 15px;
  color: white;
  font-family: inherit;
  outline: none;
  transition: all 0.3s;
}
.glass-input:focus {
  border-color: #00f2ff;
  background: rgba(0, 0, 0, 0.5);
  box-shadow: 0 0 10px rgba(0, 242, 255, 0.1);
}

/* 日期选择器美化 */
.date-picker {
  color: #fff;
  color-scheme: dark; /* 关键：强制深色原生控件 */
}

.action-btn {
  margin-top: 10px;
  background: linear-gradient(135deg, #0066ff, #00ccff);
  border: none; padding: 14px;
  border-radius: 8px; color: white; font-weight: bold;
  cursor: pointer; display: flex; justify-content: center; gap: 10px;
  transition: all 0.2s;
}
.action-btn:hover { transform: translateY(-2px); box-shadow: 0 5px 15px rgba(0, 102, 255, 0.4); }

/* --- 任务列表 --- */
.todo-list {
  display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 20px; padding-bottom: 40px;
}

.state-text { text-align: center; color: #607080; grid-column: 1/-1; padding: 20px; }

.todo-item {
  padding: 20px;
  display: flex; flex-direction: column; justify-content: space-between;
  min-height: 160px; cursor: pointer;
  transition: transform 0.2s;
}

.item-header { display: flex; justify-content: space-between; margin-bottom: 10px; color: #506080; font-size: 12px; }
.del-btn { background: none; border: none; color: #ff4444; cursor: pointer; padding: 5px; opacity: 0.6; transition: opacity 0.2s; }
.del-btn:hover { opacity: 1; }

.item-body h4 { font-size: 18px; margin-bottom: 6px; font-weight: 600; }
.item-body p { font-size: 14px; color: #b0c0d0; line-height: 1.4; }

.item-footer {
  margin-top: 15px; padding-top: 15px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  display: flex; justify-content: space-between; align-items: center;
}

.status-badge {
  font-size: 11px; padding: 4px 8px; border-radius: 4px; font-weight: bold;
}
.status-badge.active { background: rgba(0, 242, 255, 0.15); color: #00f2ff; border: 1px solid rgba(0, 242, 255, 0.3); }
.status-badge.done { background: rgba(0, 255, 100, 0.15); color: #00ff66; border: 1px solid rgba(0, 255, 100, 0.3); }

.time-badge {
  font-size: 12px; color: #a0c0ff; display: flex; align-items: center; gap: 5px;
}
.time-badge.warn { color: #ff4444; animation: pulse 1s infinite; }
@keyframes pulse { 0% { opacity: 1; } 50% { opacity: 0.5; } 100% { opacity: 1; } }

.is-done { opacity: 0.6; border-color: #00ff66; }
.is-done h4 { text-decoration: line-through; }

@media (max-width: 768px) {
  .layout-grid { flex-direction: column; overflow-y: auto; }
  .sidebar { width: 100%; height: auto; padding: 15px; flex-direction: row; align-items: center; justify-content: space-between; }
  .nav-menu { flex-direction: row; }
  .nav-menu span, .user-profile { display: none; }
  .main-content { padding: 20px; }
}
</style>