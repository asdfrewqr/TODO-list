<script setup>
import { ref, onMounted, computed } from 'vue';
import axios from 'axios';

// --- 1. 状态管理 ---
const todos = ref([]);
const newTodoTitle = ref('');
const newTodoContent = ref('');
const newTodoDeadline = ref('');
const newTodoCategory = ref('Life');
const newTodoPriority = ref(4);

const loading = ref(false);
const statusFilter = ref('all');
const categoryFilter = ref('All');
const searchQuery = ref(''); // 新增：搜索关键词

const API_URL = 'http://127.0.0.1:8000/todos';

// 静态配置
const categories = ['Work', 'Study', 'Life'];
const priorities = [
  { 'value': 1, 'label': 'Urgent & Important', 'color': '#FF3B30' },
  { 'value': 2, 'label': 'Important', 'color': '#FF9500' },
  { 'value': 3, 'label': 'Urgent', 'color': '#007AFF' },
  { 'value': 4, 'label': 'Normal', 'color': '#8E8E93' }
];

// --- 2. 核心逻辑 ---

const fetchTodos = function() {
  loading.value = true;
  axios.get(API_URL)
    .then(function(res) {
      todos.value = res.data;
    })
    .catch(function(err) { console.error(err); })
    .finally(function() { loading.value = false; });
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
    deadline: deadlineISO,
    category: newTodoCategory.value,
    priority: parseInt(newTodoPriority.value)
  })
  .then(function(res) {
    todos.value.push(res.data);
    newTodoTitle.value = '';
    newTodoContent.value = '';
    newTodoDeadline.value = '';
    newTodoCategory.value = 'Life';
    newTodoPriority.value = 4;
  })
  .catch(function(err) {
    alert('Failed to add task');
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

const updateTask = function(todo, field, value) {
  const original = todo[field];
  todo[field] = value;

  let payload = {};
  payload[field] = value;

  axios.patch(API_URL + '/' + todo.id, payload)
    .catch(function(err) {
      todo[field] = original;
      alert('Update failed');
    });
};

const deleteTodo = function(id) {
  if (!confirm('Delete this task?')) return;
  axios.delete(API_URL + '/' + id)
    .then(function() {
      todos.value = todos.value.filter(function(t) { return t.id !== id; });
    })
    .catch(function(err) { console.error(err); });
};

const getCountdown = function(deadlineStr) {
  if (!deadlineStr) return null;
  let clean = deadlineStr;
  if (clean.indexOf('Z') === -1 && clean.indexOf('+') === -1) clean += 'Z';

  const diff = new Date(clean) - new Date();
  if (diff < 0) return { overdue: true, text: 'Overdue' };

  const d = Math.floor(diff / (86400000));
  const h = Math.floor((diff % 86400000) / 3600000);
  return { overdue: false, text: d > 0 ? d + 'd ' + h + 'h' : h + 'h left' };
};

// --- 计算属性 ---

const completedCount = computed(function() { return todos.value.filter(function(t) { return t.is_completed; }).length; });
const pendingCount = computed(function() { return todos.value.filter(function(t) { return !t.is_completed; }).length; });
const totalCount = computed(function() { return todos.value.length; });

const filteredTodos = computed(function() {
  let result = todos.value;

  // 1. 搜索过滤 (新增)
  if (searchQuery.value.trim()) {
    const query = searchQuery.value.toLowerCase();
    result = result.filter(function(t) {
      return t.title.toLowerCase().includes(query);
    });
  }

  // 2. 状态筛选
  if (statusFilter.value === 'active') {
    result = result.filter(function(t) { return !t.is_completed; });
  } else if (statusFilter.value === 'completed') {
    result = result.filter(function(t) { return t.is_completed; });
  }

  // 3. 分类筛选
  if (categoryFilter.value !== 'All') {
    result = result.filter(function(t) { return t.category === categoryFilter.value; });
  }

  // 4. 排序
  return result.sort(function(a, b) {
    if (categoryFilter.value === 'All') {
      if (a.category !== b.category) return a.category.localeCompare(b.category);
    }
    return a.priority - b.priority;
  });
});

// --- 交互特效 ---
const handleCardMove = function(e) {
  const card = e.currentTarget;
  card.style.transform = 'translateY(-2px)';
  card.style.boxShadow = '0 10px 25px rgba(0, 122, 255, 0.15)';
  card.style.zIndex = '10';
};

const handleCardLeave = function(e) {
  const card = e.currentTarget;
  card.style.transform = 'translateY(0)';
  card.style.boxShadow = '0 4px 12px rgba(0, 0, 0, 0.05)';
  card.style.zIndex = '1';
};

onMounted(function() {
  fetchTodos();
});
</script>

<template>
  <div class="app-container">
    <!-- 动态背景 -->
    <div class="aurora-bg"></div>

    <div class="layout-grid">
      <!-- 侧边栏 -->
      <aside class="sidebar">
        <div class="window-controls">
          <span class="dot red"></span>
          <span class="dot yellow"></span>
          <span class="dot green"></span>
        </div>

        <div class="logo">
          <div class="logo-icon"><i class="fas fa-check"></i></div>
          <span>Reminders</span>
        </div>

        <nav class="nav-menu">
          <div class="nav-group">
            <label>STATUS</label>
            <div class="nav-item" :class="{ active: statusFilter === 'all' }" @click="statusFilter = 'all'">
              <div class="icon-wrap gray"><i class="fas fa-inbox"></i></div>
              <span>All</span>
              <span class="count">{{ totalCount }}</span>
            </div>
            <div class="nav-item" :class="{ active: statusFilter === 'active' }" @click="statusFilter = 'active'">
              <div class="icon-wrap orange"><i class="fas fa-calendar-day"></i></div>
              <span>Scheduled</span>
              <span class="count">{{ pendingCount }}</span>
            </div>
            <div class="nav-item" :class="{ active: statusFilter === 'completed' }" @click="statusFilter = 'completed'">
              <div class="icon-wrap green"><i class="fas fa-check-circle"></i></div>
              <span>Done</span>
              <span class="count">{{ completedCount }}</span>
            </div>
          </div>

          <div class="nav-group mt-4">
            <label>LISTS</label>
            <div class="nav-item" :class="{ active: categoryFilter === 'All' }" @click="categoryFilter = 'All'">
              <i class="fas fa-layer-group nav-icon"></i><span>All Lists</span>
            </div>
            <div class="nav-item" :class="{ active: categoryFilter === 'Work' }" @click="categoryFilter = 'Work'">
              <i class="fas fa-briefcase nav-icon" style="color: #007AFF"></i><span>Work</span>
            </div>
            <div class="nav-item" :class="{ active: categoryFilter === 'Study' }" @click="categoryFilter = 'Study'">
              <i class="fas fa-book nav-icon" style="color: #FF9500"></i><span>Study</span>
            </div>
            <div class="nav-item" :class="{ active: categoryFilter === 'Life' }" @click="categoryFilter = 'Life'">
              <i class="fas fa-home nav-icon" style="color: #30D158"></i><span>Life</span>
            </div>
          </div>
        </nav>

        <div class="user-card">
          <div class="avatar">AM</div>
          <div class="user-details">
            <span class="name">Alex Morgan</span>
            <span class="role">iCloud</span>
          </div>
        </div>
      </aside>

      <!-- 主内容区 -->
      <main class="main-content">
        <header class="top-bar">
          <div class="title-area">
            <h1>Tasks</h1>
            <p class="date-today">{{ new Date().toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' }) }}</p>
          </div>
          <div class="search-bar">
            <i class="fas fa-search"></i>
            <!-- 启用搜索输入框并绑定模型 -->
            <input v-model="searchQuery" placeholder="Search tasks...">
          </div>
        </header>

        <!-- 统计概览 -->
        <div class="stats-row">
          <div class="stat-card" @mousemove="handleCardMove" @mouseleave="handleCardLeave">
            <div class="stat-icon blue"><i class="fas fa-inbox"></i></div>
            <div class="stat-number">{{ totalCount }}</div>
            <div class="stat-label">Total</div>
          </div>
          <div class="stat-card orange" @mousemove="handleCardMove" @mouseleave="handleCardLeave">
            <div class="stat-icon"><i class="fas fa-clock"></i></div>
            <div class="stat-number">{{ pendingCount }}</div>
            <div class="stat-label">Pending</div>
          </div>
          <div class="stat-card green" @mousemove="handleCardMove" @mouseleave="handleCardLeave">
            <div class="stat-icon"><i class="fas fa-check-circle"></i></div>
            <div class="stat-number">{{ completedCount }}</div>
            <div class="stat-label">Completed</div>
          </div>
        </div>

        <!-- 添加任务 -->
        <div class="input-module apple-panel">
          <div class="module-header">New Reminder</div>

          <div class="input-form">
            <div class="form-group">
              <input v-model="newTodoTitle" placeholder="Title" class="apple-input title-input" @keyup.enter="addTodo">
            </div>

            <div class="form-group">
              <input v-model="newTodoContent" placeholder="Notes" class="apple-input" @keyup.enter="addTodo">
            </div>

            <div class="form-row">
              <div class="form-group col">
                <label>Date</label>
                <input type="datetime-local" v-model="newTodoDeadline" class="apple-input date-picker">
              </div>
              <div class="form-group col">
                <label>List</label>
                <select v-model="newTodoCategory" class="apple-input apple-select">
                  <option v-for="cat in categories" :key="cat" :value="cat">{{ cat }}</option>
                </select>
              </div>
              <div class="form-group col">
                <label>Priority</label>
                <select v-model="newTodoPriority" class="apple-input apple-select">
                  <option v-for="p in priorities" :key="p.value" :value="p.value">{{ p.label }}</option>
                </select>
              </div>
              <div class="form-group btn-container">
                <button class="apple-btn" @click="addTodo">Add</button>
              </div>
            </div>
          </div>
        </div>

        <!-- 任务列表 -->
        <div class="todo-list">
          <div v-if="loading" class="state-text">Syncing...</div>
          <div v-else-if="filteredTodos.length === 0" class="state-text">
            <span v-if="searchQuery">No tasks match "{{ searchQuery }}"</span>
            <span v-else>No reminders found.</span>
          </div>

          <div
            v-for="todo in filteredTodos"
            :key="todo.id"
            class="todo-item apple-panel"
            :class="{ 'is-done': todo.is_completed }"
            @mousemove="handleCardMove"
            @mouseleave="handleCardLeave"
          >
            <div class="item-left">
              <div class="checkbox-circle" :class="{ checked: todo.is_completed }" @click="toggleTodo(todo)">
                <i class="fas fa-check" v-if="todo.is_completed"></i>
              </div>

              <div class="item-content">
                <div class="item-header-row">
                  <h4>{{ todo.title }}</h4>
                  <!-- 优先级标签 -->
                  <span
                    class="priority-dot"
                    :style="{ backgroundColor: priorities.find(function(p) { return p.value === todo.priority })?.color }"
                    title="Priority"
                  ></span>
                </div>

                <p v-if="todo.description">{{ todo.description }}</p>

                <div class="item-meta">
                  <!-- 截止日期标签 -->
                  <span v-if="todo.deadline && !todo.is_completed" class="meta-tag deadline" :class="{ 'overdue': getCountdown(todo.deadline).overdue }">
                    <i class="far fa-clock"></i> {{ getCountdown(todo.deadline).text }}
                  </span>

                  <!-- 分类标签 -->
                  <span class="meta-tag category">
                    {{ todo.category }}
                  </span>

                  <!-- 可修改优先级的下拉 (隐式) -->
                  <select
                    class="mini-select"
                    :value="todo.priority"
                    @change="(e) => updateTask(todo, 'priority', parseInt(e.target.value))"
                    @click.stop
                    title="Change Priority"
                  >
                    <option v-for="p in priorities" :key="p.value" :value="p.value">P{{ p.value }}</option>
                  </select>
                </div>
              </div>
            </div>

            <div class="item-right">
              <button class="icon-btn delete" @click.stop="deleteTodo(todo.id)">
                <i class="far fa-trash-alt"></i>
              </button>
            </div>
          </div>
        </div>
      </main>
    </div>
  </div>
</template>

<style>
/* 全局设置 */
* { margin: 0; padding: 0; box-sizing: border-box; }
html, body {
  width: 100%; height: 100%; overflow: hidden;
  font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
}
</style>

<style scoped>
@import url("https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css");

:root {
  /* Apple System Colors */
  --apple-blue: #007AFF;
  --apple-red: #FF453A;
  --apple-green: #30D158;
  --apple-orange: #FF9F0A;
  --apple-gray: #8E8E93;
  --apple-bg-glass: rgba(255, 255, 255, 0.65);
  --text-primary: #1d1d1f;
  --text-secondary: #86868b;
  --border-light: rgba(0, 0, 0, 0.05);
}

.app-container {
  width: 100%; height: 100%;
  position: fixed; top: 0; left: 0;
  background: #F2F6FF; /* 极淡的蓝灰色底 */
}

/* 极光背景 (淡蓝紫色系，清爽风格) */
.aurora-bg {
  position: absolute; top: 0; left: 0; width: 100%; height: 100%;
  background:
    radial-gradient(circle at 10% 10%, #D0E8FF 0%, transparent 50%),
    radial-gradient(circle at 90% 90%, #E8E0FF 0%, transparent 50%),
    radial-gradient(circle at 50% 50%, #FFFFFF 0%, transparent 80%);
  z-index: 0;
  filter: blur(60px);
}

.layout-grid {
  position: relative; z-index: 2;
  display: flex; width: 100%; height: 100%;
}

/* --- 侧边栏 (macOS Sidebar) --- */
.sidebar {
  width: 260px; height: 100%;
  background: rgba(255, 255, 255, 0.5); /* 高透亮白 */
  backdrop-filter: blur(30px) saturate(150%);
  -webkit-backdrop-filter: blur(30px) saturate(150%);
  border-right: 1px solid rgba(0,0,0,0.05);
  display: flex; flex-direction: column; padding: 20px; flex-shrink: 0;
}

.window-controls { display: flex; gap: 8px; margin-bottom: 20px; }
.dot { width: 12px; height: 12px; border-radius: 50%; }
.red { background: #FF5F56; }
.yellow { background: #FFBD2E; }
.green { background: #27C93F; }

.logo {
  display: flex; align-items: center; gap: 10px;
  font-size: 18px; font-weight: 600; color: #333; margin-bottom: 30px;
  opacity: 0.9;
}
.logo-icon { width: 28px; height: 28px; background: var(--apple-blue); color: white; border-radius: 7px; display: flex; align-items: center; justify-content: center; font-size: 14px; }

.nav-menu { flex: 1; display: flex; flex-direction: column; gap: 20px; }
.nav-group label {
  display: block; font-size: 11px; font-weight: 600; color: var(--apple-gray);
  margin-bottom: 5px; padding-left: 10px;
}
.mt-4 { margin-top: 20px; }

.nav-item {
  display: flex; align-items: center; gap: 10px;
  padding: 8px 10px; margin-bottom: 2px;
  border-radius: 6px; cursor: pointer;
  transition: background 0.15s;
  color: #444; font-size: 14px; font-weight: 500;
}
.nav-item:hover { background: rgba(0,0,0,0.05); }
.nav-item.active { background: rgba(0,0,0,0.08); color: #000; }

.icon-wrap {
  width: 24px; height: 24px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: 12px; color: white;
}
.nav-icon { width: 24px; text-align: center; font-size: 16px; color: var(--apple-gray); }
.icon-wrap.gray { background: var(--apple-gray); }
.icon-wrap.orange { background: var(--apple-orange); }
.icon-wrap.green { background: var(--apple-green); }

.count { margin-left: auto; color: var(--apple-gray); font-size: 13px; }

.user-profile {
  margin-top: auto; display: flex; align-items: center; gap: 10px;
  padding: 10px; border-top: 1px solid var(--border-light);
}
.avatar {
  width: 32px; height: 32px; background: var(--apple-gray); border-radius: 50%;
  display: flex; align-items: center; justify-content: center; font-size: 12px; font-weight: bold; color: white;
}
.user-details { display: flex; flex-direction: column; }
.name { font-size: 13px; font-weight: 500; }
.role { font-size: 11px; color: var(--apple-gray); }

/* --- 主内容区 --- */
.main-content {
  flex: 1; padding: 40px 50px; overflow-y: auto;
  display: flex; flex-direction: column; gap: 25px;
}

.top-bar { margin-bottom: 10px; display: flex; justify-content: space-between; align-items: flex-end; }
.top-bar h1 { font-size: 32px; font-weight: 700; color: var(--apple-blue); margin-bottom: 2px; }
.date-today { font-size: 18px; color: var(--apple-red); font-weight: 500; }

.search-bar {
  display: flex; align-items: center; gap: 8px;
  background: rgba(0,0,0,0.05);
  padding: 6px 10px; border-radius: 8px; width: 200px;
}
.search-bar i { color: var(--apple-gray); font-size: 13px; }
.search-bar input {
  background: transparent; border: none; color: #333; font-size: 13px; width: 100%; outline: none;
}

/* 统计卡片 */
.stats-row { display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; margin-bottom: 10px; }
.stat-card {
  background: rgba(255, 255, 255, 0.8);
  border-radius: 12px; padding: 15px;
  display: flex; flex-direction: column;
  border: 1px solid white;
  box-shadow: 0 2px 10px rgba(0,0,0,0.05);
  backdrop-filter: blur(20px); transition: all 0.2s;
  height: 100px; justify-content: space-between;
}
.stat-icon { font-size: 18px; width: 30px; height: 30px; border-radius: 50%; display: flex; align-items: center; justify-content: center; color: white; }
.stat-card.blue .stat-icon { background: var(--apple-blue); }
.stat-card.orange .stat-icon { background: var(--apple-orange); }
.stat-card.green .stat-icon { background: var(--apple-green); }
.stat-number { font-size: 28px; font-weight: 700; color: #333; margin-left: auto; margin-top: -30px; }
.stat-label { font-size: 13px; color: var(--apple-gray); font-weight: 600; }

/* 输入模块 */
.apple-panel {
  background: rgba(255, 255, 255, 0.8);
  border-radius: 12px;
  border: 1px solid white;
  backdrop-filter: blur(20px);
  padding: 20px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05);
}

.input-module { display: flex; flex-direction: column; gap: 15px; }
.module-header { font-size: 15px; font-weight: 600; color: #333; border-bottom: 1px solid rgba(0,0,0,0.05); padding-bottom: 10px; margin-bottom: 5px; }

.form-group { margin-bottom: 12px; }
.form-row { display: flex; gap: 12px; align-items: flex-end; }
.col { flex: 1; }
.btn-container { width: 100px; }
label { display: block; font-size: 11px; color: var(--apple-gray); margin-bottom: 4px; font-weight: 600; }

.apple-input {
  width: 100%;
  background: rgba(0, 0, 0, 0.03);
  border: 1px solid rgba(0, 0, 0, 0.05);
  border-radius: 8px;
  padding: 10px 12px;
  color: #333; font-size: 14px;
  outline: none; transition: border 0.2s;
}
.apple-input:focus { border-color: var(--apple-blue); background: white; box-shadow: 0 0 0 3px rgba(10,132,255,0.1); }
.title-input { font-weight: 600; font-size: 15px; }
.apple-select { appearance: none; cursor: pointer; }

.apple-btn {
  width: 100%; height: 38px;
  background: var(--apple-blue); color: white;
  border: none; border-radius: 8px;
  font-size: 13px; font-weight: 600; cursor: pointer;
  transition: background 0.2s;
}
.apple-btn:hover { background: #0062cc; }
.apple-btn:active { transform: scale(0.96); }

/* 任务列表 */
.todo-list { display: flex; flex-direction: column; gap: 10px; padding-bottom: 40px; }
.state-text { text-align: center; color: var(--apple-gray); padding: 20px; }

.todo-item {
  display: flex; align-items: center; justify-content: space-between;
  padding: 16px; transition: all 0.2s; cursor: default;
}
.is-done { opacity: 0.5; }
.is-done h4 { text-decoration: line-through; color: var(--apple-gray); }

.item-left { display: flex; align-items: flex-start; gap: 15px; flex: 1; }
.checkbox-circle {
  width: 22px; height: 22px; border-radius: 50%; border: 1.5px solid #c7c7cc;
  display: flex; align-items: center; justify-content: center; cursor: pointer;
  flex-shrink: 0; margin-top: 2px;
}
.checkbox-circle.checked { background: var(--apple-blue); border-color: var(--apple-blue); color: white; font-size: 12px; }

.item-content { flex: 1; }
.item-header-row { display: flex; align-items: center; gap: 8px; margin-bottom: 2px; }
.priority-dot { width: 8px; height: 8px; border-radius: 50%; display: inline-block; }

.item-content h4 { font-size: 15px; font-weight: 500; margin: 0; }
.item-content p { font-size: 13px; color: var(--apple-gray); line-height: 1.4; margin-bottom: 4px; }

.item-meta { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
.meta-tag { font-size: 10px; padding: 2px 6px; border-radius: 4px; font-weight: 600; letter-spacing: 0.3px; text-transform: uppercase; }
.deadline-tag { color: var(--apple-blue); background: rgba(10, 132, 255, 0.1); }
.deadline-tag.overdue { color: var(--apple-red); background: rgba(255, 69, 58, 0.1); }
.category { color: #8E8E93; background: rgba(0,0,0,0.05); }

.mini-select { border: none; background: transparent; font-size: 10px; color: #888; cursor: pointer; }

.icon-btn {
  background: transparent; border: none; color: #c7c7cc;
  width: 30px; height: 30px; border-radius: 50%;
  cursor: pointer; transition: color 0.2s;
}
.icon-btn:hover { color: var(--apple-red); background: rgba(255, 69, 58, 0.1); }

@media (max-width: 768px) {
  .layout-grid { flex-direction: column; overflow-y: auto; }
  .sidebar { width: 100%; height: auto; padding: 15px; flex-direction: row; align-items: center; justify-content: space-between; }
  .window-controls, .nav-menu, .user-profile { display: none; }
  .main-content { padding: 20px; }
  .stats-row { grid-template-columns: 1fr; }
  .form-row { flex-direction: column; gap: 10px; }
  .btn-container { width: 100%; }
}
</style>