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

const API_URL = 'http://127.0.0.1:8000/todos';

// 静态配置 (给属性名加上引号以兼容严格解析器)
const categories = ['Work', 'Study', 'Life'];
const priorities = [
  { 'value': 1, 'label': 'P1: 重要且紧急', 'color': '#ff4d4f' },
  { 'value': 2, 'label': 'P2: 重要不紧急', 'color': '#ffa940' },
  { 'value': 3, 'label': 'P3: 紧急不重要', 'color': '#36cfc9' },
  { 'value': 4, 'label': 'P4: 不重要不紧急', 'color': '#bfbfbf' }
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
    // 重置表单
    newTodoTitle.value = '';
    newTodoContent.value = '';
    newTodoDeadline.value = '';
    newTodoCategory.value = 'Life';
    newTodoPriority.value = 4;
  })
  .catch(function(err) {
    alert('Add task failed');
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

// --- 辅助函数 ---
const getCountdown = function(deadlineStr) {
  if (!deadlineStr) return null;
  let clean = deadlineStr;
  if (clean.indexOf('Z') === -1 && clean.indexOf('+') === -1) clean += 'Z';
  const diff = new Date(clean) - new Date();
  if (diff < 0) return { overdue: true, text: 'TIMEOUT' };

  const d = Math.floor(diff / (86400000));
  const h = Math.floor((diff % 86400000) / 3600000);
  return { overdue: false, text: d > 0 ? d + 'd ' + h + 'h left' : h + 'h left' };
};

// --- 计算属性 ---

const completedCount = computed(function() { return todos.value.filter(function(t) { return t.is_completed; }).length; });
const pendingCount = computed(function() { return todos.value.filter(function(t) { return !t.is_completed; }).length; });
const totalCount = computed(function() { return todos.value.length; });

const filteredTodos = computed(function() {
  let result = todos.value;

  if (statusFilter.value === 'active') {
    result = result.filter(function(t) { return !t.is_completed; });
  } else if (statusFilter.value === 'completed') {
    result = result.filter(function(t) { return t.is_completed; });
  }

  if (categoryFilter.value !== 'All') {
    result = result.filter(function(t) { return t.category === categoryFilter.value; });
  }

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
  const rect = card.getBoundingClientRect();
  const x = e.clientX - rect.left;
  const y = e.clientY - rect.top;
  const rotateY = (x / rect.width - 0.5) * 5;
  const rotateX = (y / rect.height - 0.5) * -5;
  card.style.transform = 'perspective(1000px) rotateX(' + rotateX + 'deg) rotateY(' + rotateY + 'deg) scale(1.01)';

  if (card.classList.contains('card-overdue')) {
    card.style.boxShadow = '0 0 25px rgba(255, 51, 51, 0.4)';
  } else {
    card.style.boxShadow = '0 0 20px rgba(0, 243, 255, 0.3)';
  }
  card.style.zIndex = '10';
};

const handleCardLeave = function(e) {
  const card = e.currentTarget;
  card.style.transform = 'perspective(1000px) rotateX(0) rotateY(0) scale(1)';
  card.style.boxShadow = '0 4px 15px rgba(0, 100, 255, 0.1)';
  card.style.zIndex = '1';
};

onMounted(function() {
  fetchTodos();
});
</script>

<template>
  <div class="app-container">
    <div class="bg-gradient"></div>

    <div class="layout-grid">
      <!-- 侧边栏 -->
      <aside class="sidebar">
        <div class="logo">
          <i class="fab fa-react fa-2x spin"></i>
          <span>BlueOS</span>
        </div>

        <nav class="nav-menu">
          <div class="menu-label">STATUS LISTS</div>
          <div class="nav-item" :class="{ active: statusFilter === 'all' }" @click="statusFilter = 'all'">
            <i class="fas fa-layer-group"></i><span>Total List</span>
          </div>
          <div class="nav-item" :class="{ active: statusFilter === 'active' }" @click="statusFilter = 'active'">
            <i class="fas fa-bolt"></i><span>Pending Tasks</span>
          </div>
          <div class="nav-item" :class="{ active: statusFilter === 'completed' }" @click="statusFilter = 'completed'">
            <i class="fas fa-check-circle"></i><span>Completed</span>
          </div>

          <div class="menu-separator"></div>

          <div class="menu-label">CATEGORY FILTER</div>
          <div class="nav-item" :class="{ active: categoryFilter === 'All' }" @click="categoryFilter = 'All'">
            <i class="fas fa-globe"></i><span>All Categories</span>
          </div>
          <div class="nav-item" :class="{ active: categoryFilter === 'Work' }" @click="categoryFilter = 'Work'">
            <i class="fas fa-briefcase"></i><span>Work</span>
          </div>
          <div class="nav-item" :class="{ active: categoryFilter === 'Study' }" @click="categoryFilter = 'Study'">
            <i class="fas fa-book"></i><span>Study</span>
          </div>
          <div class="nav-item" :class="{ active: categoryFilter === 'Life' }" @click="categoryFilter = 'Life'">
            <i class="fas fa-coffee"></i><span>Life</span>
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
          <div class="system-status"><span class="status-dot"></span> ONLINE</div>
        </header>

        <!-- 统计卡片 -->
        <div class="stats-row">
          <div class="stat-card blue" @mousemove="handleCardMove" @mouseleave="handleCardLeave">
            <div class="icon-box"><i class="fas fa-tasks"></i></div>
            <div class="stat-info"><h3>{{ totalCount }}</h3><p>Total</p></div>
          </div>
          <div class="stat-card cyan" @mousemove="handleCardMove" @mouseleave="handleCardLeave">
            <div class="icon-box"><i class="fas fa-clock"></i></div>
            <div class="stat-info"><h3>{{ pendingCount }}</h3><p>Pending</p></div>
          </div>
          <div class="stat-card indigo" @mousemove="handleCardMove" @mouseleave="handleCardLeave">
            <div class="icon-box"><i class="fas fa-check"></i></div>
            <div class="stat-info"><h3>{{ completedCount }}</h3><p>Completed</p></div>
          </div>
        </div>

        <!-- 输入模块 (纵向) -->
        <div class="input-module glass-panel">
          <div class="module-title"><i class="fas fa-plus-circle"></i> Create New Task</div>
          <div class="input-stack">
            <input v-model="newTodoTitle" placeholder="Task Title..." class="glass-input" @keyup.enter="addTodo">
            <input v-model="newTodoContent" placeholder="Description..." class="glass-input" @keyup.enter="addTodo">

            <!-- 设置行：时间、分类、优先级 -->
            <div class="settings-row">
              <div class="input-group">
                <label>Deadline</label>
                <input type="datetime-local" v-model="newTodoDeadline" class="glass-input date-picker">
              </div>
              <div class="input-group">
                <label>Category</label>
                <select v-model="newTodoCategory" class="glass-input select-input">
                  <option v-for="cat in categories" :key="cat" :value="cat">{{ cat }}</option>
                </select>
              </div>
              <div class="input-group">
                <label>Priority (Eisenhower)</label>
                <select v-model="newTodoPriority" class="glass-input select-input">
                  <option v-for="p in priorities" :key="p.value" :value="p.value">{{ p.label }}</option>
                </select>
              </div>
            </div>

            <button class="action-btn" @click="addTodo">Create Task <i class="fas fa-arrow-right"></i></button>
          </div>
        </div>

        <!-- 任务列表 -->
        <div class="todo-list">
          <div v-if="loading" class="state-text">Loading data...</div>
          <div v-else-if="filteredTodos.length === 0" class="state-text">No tasks found in current view.</div>

          <div
            v-for="todo in filteredTodos"
            :key="todo.id"
            class="todo-item glass-panel"
            :class="{
              'is-done': todo.is_completed,
              'card-overdue': !todo.is_completed && getCountdown(todo.deadline)?.overdue
            }"
            @mousemove="handleCardMove"
            @mouseleave="handleCardLeave"
          >
            <!-- 卡片头部: ID和删除 -->
            <div class="item-header">
              <span class="id-tag">#{{ todo.id }}</span>
              <button class="del-btn" @click.stop="deleteTodo(todo.id)"><i class="fas fa-times"></i></button>
            </div>

            <!-- 卡片主体: 标题和描述 -->
            <div class="item-body" @click="toggleTodo(todo)">
              <h4>{{ todo.title }}</h4>
              <p>{{ todo.description || 'No description' }}</p>
            </div>

            <!-- 卡片底部: 属性设置与状态 -->
            <div class="item-footer">
              <div class="meta-controls">
                <!-- 分类标签 (可点击修改) -->
                <div class="meta-group">
                  <i class="fas fa-tag"></i>
                  <select
                    class="mini-select"
                    :value="todo.category"
                    @change="(e) => updateTask(todo, 'category', e.target.value)"
                    @click.stop
                  >
                    <option v-for="cat in categories" :key="cat" :value="cat">{{ cat }}</option>
                  </select>
                </div>

                <!-- 优先级标签 (可点击修改) -->
                <div class="meta-group" :style="{ color: priorities.find(p => p.value === todo.priority)?.color }">
                  <i class="fas fa-flag"></i>
                  <select
                    class="mini-select priority-select"
                    :value="todo.priority"
                    @change="(e) => updateTask(todo, 'priority', parseInt(e.target.value))"
                    @click.stop
                  >
                    <option v-for="p in priorities" :key="p.value" :value="p.value">P{{ p.value }}</option>
                  </select>
                </div>
              </div>

              <div class="status-group">
                <div v-if="todo.deadline && !todo.is_completed"
                     class="time-badge"
                     :class="{ 'warn': getCountdown(todo.deadline).overdue }">
                  <i class="far fa-clock"></i> {{ getCountdown(todo.deadline).text }}
                </div>
                <div class="status-badge" :class="todo.is_completed ? 'done' : 'active'">
                  {{ todo.is_completed ? 'DONE' : 'ACTIVE' }}
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  </div>
</template>

<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
html, body { width: 100%; height: 100%; overflow: hidden; font-family: 'Segoe UI', sans-serif; }
</style>

<style scoped>
@import url("https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css");

:root {
  --primary: #00f2ff;
  --secondary: #0066ff;
  --glass-bg: rgba(255, 255, 255, 0.1);
  --panel-bg: rgba(10, 20, 40, 0.7);
}

.app-container {
  width: 100%; height: 100%;
  background-color: #050a14; color: white;
  position: fixed; top: 0; left: 0;
}

.bg-gradient {
  position: absolute; top: -50%; left: -50%; width: 200%; height: 200%;
  background: radial-gradient(circle at 50% 50%, rgba(0, 102, 255, 0.15), transparent 60%),
              radial-gradient(circle at 80% 20%, rgba(0, 242, 255, 0.1), transparent 40%);
  z-index: 0; animation: rotate 60s linear infinite;
}
@keyframes rotate { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }

.layout-grid {
  position: relative; z-index: 1; display: flex; width: 100%; height: 100%;
}

/* 侧边栏 */
.sidebar {
  width: 260px; height: 100%;
  background: rgba(10, 25, 50, 0.85); backdrop-filter: blur(20px);
  border-right: 1px solid rgba(100, 200, 255, 0.1);
  display: flex; flex-direction: column; padding: 20px; flex-shrink: 0;
}

.logo {
  display: flex; align-items: center; gap: 10px;
  font-size: 24px; font-weight: bold; color: #00f2ff; margin-bottom: 30px; padding-left: 10px;
}
.spin { animation: spin 10s linear infinite; }
@keyframes spin { 100% { transform: rotate(360deg); } }

.nav-menu { display: flex; flex-direction: column; gap: 5px; flex: 1; }
.menu-label { font-size: 11px; color: #506080; font-weight: bold; margin-top: 20px; margin-bottom: 5px; letter-spacing: 1px; }
.menu-separator { height: 1px; background: rgba(255,255,255,0.1); margin: 10px 0; }

.nav-item {
  display: flex; align-items: center; gap: 12px; padding: 10px 15px;
  border-radius: 8px; cursor: pointer; transition: all 0.3s; color: #a0b0c0; font-weight: 500;
}
.nav-item:hover { background: rgba(0, 242, 255, 0.1); color: white; }
.nav-item.active { background: linear-gradient(90deg, rgba(0, 102, 255, 0.2), transparent); border-left: 3px solid #00f2ff; color: #00f2ff; }

.user-profile {
  margin-top: auto; display: flex; align-items: center; gap: 12px; padding: 15px;
  background: rgba(255, 255, 255, 0.05); border-radius: 12px;
}
.avatar { width: 36px; height: 36px; background: #0066ff; border-radius: 50%; }
.user-details { display: flex; flex-direction: column; }
.name { font-size: 14px; font-weight: bold; }
.role { font-size: 12px; color: #00f2ff; }

/* 主内容区 */
.main-content {
  flex: 1; padding: 30px 40px; overflow-y: auto;
  display: flex; flex-direction: column; gap: 25px;
}

.top-bar { display: flex; justify-content: space-between; align-items: center; }
h1 { font-size: 28px; font-weight: 600; color: #e0f0ff; }
.system-status { display: flex; align-items: center; gap: 8px; font-size: 12px; color: #00f2ff; font-weight: bold; }
.status-dot { width: 8px; height: 8px; background: #00f2ff; border-radius: 50%; box-shadow: 0 0 10px #00f2ff; }

.stats-row { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 20px; }
.stat-card {
  padding: 20px; border-radius: 16px; display: flex; align-items: center; gap: 20px;
  background: rgba(20, 40, 70, 0.6); border: 1px solid rgba(100, 200, 255, 0.2);
  backdrop-filter: blur(10px); transition: transform 0.2s;
}
.icon-box {
  width: 50px; height: 50px; border-radius: 12px; display: flex; align-items: center; justify-content: center;
  font-size: 20px; background: rgba(255, 255, 255, 0.1);
}
.blue .icon-box { color: #00f2ff; box-shadow: 0 0 15px rgba(0, 242, 255, 0.2); }
.cyan .icon-box { color: #00aaff; box-shadow: 0 0 15px rgba(0, 170, 255, 0.2); }
.indigo .icon-box { color: #6699ff; box-shadow: 0 0 15px rgba(102, 153, 255, 0.2); }
.stat-info h3 { font-size: 24px; font-weight: bold; }
.stat-info p { font-size: 13px; color: #a0c0ff; }

.glass-panel {
  background: rgba(20, 30, 50, 0.7); border: 1px solid rgba(100, 200, 255, 0.2);
  backdrop-filter: blur(10px); border-radius: 16px;
}

.input-module { padding: 25px; }
.module-title { color: #00f2ff; font-weight: bold; margin-bottom: 20px; display: flex; align-items: center; gap: 8px; }
.input-stack { display: flex; flex-direction: column; gap: 15px; }
.settings-row { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 15px; }
.input-group { display: flex; flex-direction: column; gap: 6px; }
.input-group label { font-size: 12px; color: #80a0c0; font-weight: 600; }

.glass-input {
  background: rgba(0, 0, 0, 0.3); border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 8px; padding: 12px 15px; color: white; font-family: inherit;
  outline: none; transition: all 0.3s;
}
.glass-input:focus { border-color: #00f2ff; background: rgba(0, 0, 0, 0.5); box-shadow: 0 0 10px rgba(0, 242, 255, 0.1); }
.select-input { appearance: none; cursor: pointer; }
.date-picker { color: #fff; color-scheme: dark; }

.action-btn {
  margin-top: 10px; background: linear-gradient(135deg, #0066ff, #00ccff);
  border: none; padding: 14px; border-radius: 8px; color: white; font-weight: bold;
  cursor: pointer; display: flex; justify-content: center; gap: 10px; transition: all 0.2s;
}
.action-btn:hover { transform: translateY(-2px); box-shadow: 0 5px 15px rgba(0, 102, 255, 0.4); }

.todo-list { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 20px; padding-bottom: 40px; }
.state-text { text-align: center; color: #607080; grid-column: 1/-1; padding: 20px; }

.todo-item {
  padding: 20px; display: flex; flex-direction: column; justify-content: space-between;
  min-height: 180px; cursor: pointer; transition: transform 0.2s; border-left: 4px solid transparent;
}
/* 卡片左侧边框对应分类颜色 */
.todo-item:has(.mini-select[value="Work"]) { border-left-color: #00f2ff; }
.todo-item:has(.mini-select[value="Study"]) { border-left-color: #ffa940; }
.todo-item:has(.mini-select[value="Life"]) { border-left-color: #36cfc9; }

.card-overdue { border-color: #ff4d4f; box-shadow: 0 0 15px rgba(255, 77, 79, 0.2); }

.item-header { display: flex; justify-content: space-between; margin-bottom: 10px; color: #506080; font-size: 12px; }
.del-btn { background: none; border: none; color: #ff4444; cursor: pointer; padding: 5px; opacity: 0.6; transition: opacity 0.2s; }
.del-btn:hover { opacity: 1; }

.item-body h4 { font-size: 18px; margin-bottom: 6px; font-weight: 600; }
.item-body p { font-size: 14px; color: #b0c0d0; line-height: 1.4; }

.item-footer {
  margin-top: 15px; padding-top: 15px; border-top: 1px solid rgba(255, 255, 255, 0.1);
  display: flex; justify-content: space-between; align-items: center;
}

.meta-controls { display: flex; gap: 10px; }
.meta-group { display: flex; align-items: center; gap: 5px; font-size: 12px; color: #8090a0; background: rgba(0,0,0,0.2); padding: 4px 8px; border-radius: 6px; }
.mini-select { background: transparent; border: none; color: inherit; font-size: 12px; cursor: pointer; outline: none; }
.priority-select { font-weight: bold; }

.status-group { display: flex; flex-direction: column; align-items: flex-end; gap: 5px; }
.status-badge { font-size: 10px; padding: 2px 6px; border-radius: 4px; font-weight: bold; }
.status-badge.active { background: rgba(0, 242, 255, 0.15); color: #00f2ff; }
.status-badge.done { background: rgba(0, 255, 100, 0.15); color: #00ff66; }

.time-badge { font-size: 11px; color: #a0c0ff; display: flex; align-items: center; gap: 4px; }
.time-badge.warn { color: #ff4d4f; font-weight: bold; animation: pulse 1s infinite; }
@keyframes pulse { 0% { opacity: 1; } 50% { opacity: 0.5; } 100% { opacity: 1; } }

.is-done { opacity: 0.6; border-color: #00ff66; }
.is-done h4 { text-decoration: line-through; }

@media (max-width: 768px) {
  .layout-grid { flex-direction: column; overflow-y: auto; }
  .sidebar { width: 100%; height: auto; padding: 15px; flex-direction: row; align-items: center; justify-content: space-between; }
  .nav-menu { display: none; } /* Mobile simplify */
  .user-profile { display: none; }
  .main-content { padding: 20px; }
  .settings-row { grid-template-columns: 1fr; }
}
</style>