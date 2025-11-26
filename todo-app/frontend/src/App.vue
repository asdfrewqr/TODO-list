<script setup>
import { ref, onMounted, onBeforeUnmount, computed } from 'vue';
import axios from 'axios';
import gsap from 'gsap';

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
const searchQuery = ref('');

const API_URL = 'http://127.0.0.1:8000/todos';

// --- 元气值系统状态 ---
const energy = ref(50);
const penalizedTasks = ref(new Set());
const showLevelUpAnim = ref(false);
let timerInterval = null; // 定时器引用

// 静态配置
const categories = ['Work', 'Study', 'Life'];
const priorities = [
  { value: 1, label: 'Urgent & Important', color: '#FF3B30' },
  { value: 2, label: 'Important', color: '#FF9500' },
  { value: 3, label: 'Urgent', color: '#007AFF' },
  { value: 4, label: 'Normal', color: '#8E8E93' }
];

// --- 2. 核心逻辑 ---

// 元气值：读取/保存
function loadEnergySystem() {
  const savedEnergy = localStorage.getItem('user_energy');
  if (savedEnergy !== null) energy.value = parseInt(savedEnergy);

  const savedPenalized = localStorage.getItem('penalized_tasks');
  if (savedPenalized) {
    try {
      penalizedTasks.value = new Set(JSON.parse(savedPenalized));
    } catch (e) {
      penalizedTasks.value = new Set();
    }
  }
}

function saveEnergySystem() {
  localStorage.setItem('user_energy', energy.value);
  const penalizedArray = Array.from(penalizedTasks.value);
  localStorage.setItem('penalized_tasks', JSON.stringify(penalizedArray));
}

// 元气值：更新 (范围限制 0-100)
function updateEnergy(amount) {
  const oldVal = energy.value;
  let newVal = oldVal + amount;

  if (newVal > 100) newVal = 100;
  if (newVal < 0) newVal = 0;

  energy.value = newVal;
  saveEnergySystem();

  // 触发动画：每增加 10 点
  if (amount > 0 && Math.floor(oldVal / 10) < Math.floor(newVal / 10)) {
    triggerMysteryAnimation();
  }
}

// 倒计时逻辑 (显示几时几分)
function getCountdown(deadlineStr) {
  if (!deadlineStr) return null;

  let cleanDeadline = deadlineStr;
  if (cleanDeadline.indexOf('Z') === -1 && cleanDeadline.indexOf('+') === -1) {
      cleanDeadline += 'Z';
  }

  const now = new Date();
  const deadline = new Date(cleanDeadline);
  const diff = deadline - now;

  if (diff < 0) return { overdue: true, text: '已超时' };

  const days = Math.floor(diff / (1000 * 60 * 60 * 24));
  const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
  const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));

  let text = '';
  if (days > 0) text += `${days}天 `;
  if (hours > 0 || days > 0) text += `${hours}小时 `;
  text += `${minutes}分钟`;

  return { overdue: false, text: text };
}

// 自动检测超时扣分 (核心逻辑)
function checkAutomaticPenalties() {
  todos.value.forEach(function(todo) {
    // 如果任务未完成 且 有截止日期
    if (!todo.is_completed && todo.deadline) {
      const result = getCountdown(todo.deadline);
      // 如果已超时 且 之前未扣过分
      if (result.overdue && !penalizedTasks.value.has(todo.id)) {
        updateEnergy(-5); // 自动扣分
        penalizedTasks.value.add(todo.id);
        saveEnergySystem();
        console.log(`Task ${todo.id} overdue. Energy penalized.`);
      }
    }
  });
}

// API 操作
function fetchTodos() {
  loading.value = true;
  axios.get(API_URL)
    .then(function(res) {
      todos.value = res.data;
      checkAutomaticPenalties();
    })
    .catch(function(err) { console.error(err); })
    .finally(function() { loading.value = false; });
}

function addTodo() {
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
  })
  .catch(function(err) {
    alert('添加任务失败');
  });
}

function toggleTodo(todo) {
  const original = todo.is_completed;
  const nextState = !original;

  // 乐观更新
  todo.is_completed = nextState;

  axios.patch(`${API_URL}/${todo.id}/toggle`)
    .then(function() {
      if (nextState === true) {
        // 任务完成：检查是否准时
        const countdown = getCountdown(todo.deadline);
        if (!todo.deadline || (countdown && !countdown.overdue)) {
          updateEnergy(5); // 准时完成 +5
        }
      } else {
        // 取消完成：扣回分数 (防止刷分)
        updateEnergy(-5);
      }
    })
    .catch(function(err) {
      todo.is_completed = original; // 失败回滚
    });
}

function updateTask(todo, field, value) {
  const original = todo[field];
  todo[field] = value;
  let payload = {};
  payload[field] = value;
  axios.patch(`${API_URL}/${todo.id}`, payload)
    .catch(function(err) { todo[field] = original; });
}

function deleteTodo(id) {
  // 增加确认提示
  if (typeof window !== 'undefined' && !confirm('确认要删除这个任务吗？\n删除后无法恢复。')) return;

  axios.delete(`${API_URL}/${id}`)
    .then(function() {
      todos.value = todos.value.filter(function(t) { return t.id !== id; });
    })
    .catch(function(err) { console.error(err); });
}

// --- 计算属性 ---
const completedCount = computed(function() { return todos.value.filter(function(t) { return t.is_completed; }).length; });
const pendingCount = computed(function() { return todos.value.filter(function(t) { return !t.is_completed; }).length; });
const totalCount = computed(function() { return todos.value.length; });

const energyStatus = computed(function() {
  if (energy.value >= 100) return { icon: '🌞', text: '元气满满', color: '#FFD700' };
  if (energy.value <= 0) return { icon: '💔', text: '心碎了', color: '#FF3B30' };
  if (energy.value >= 80) return { icon: '⚡', text: '能量爆棚', color: '#30D158' };
  if (energy.value >= 40) return { icon: '✨', text: '状态不错', color: '#007AFF' };
  return { icon: '☁️', text: '需要休息', color: '#8E8E93' };
});

const filteredTodos = computed(function() {
  let result = todos.value;
  if (searchQuery.value.trim()) {
    const query = searchQuery.value.toLowerCase();
    result = result.filter(function(t) { return t.title.toLowerCase().includes(query); });
  }
  if (statusFilter.value === 'active') result = result.filter(function(t) { return !t.is_completed; });
  else if (statusFilter.value === 'completed') result = result.filter(function(t) { return t.is_completed; });
  if (categoryFilter.value !== 'All') result = result.filter(function(t) { return t.category === categoryFilter.value; });

  return result.sort(function(a, b) {
    if (categoryFilter.value === 'All' && a.category !== b.category) return a.category.localeCompare(b.category);
    return a.priority - b.priority;
  });
});

// --- 交互特效 ---
function triggerMysteryAnimation() {
  showLevelUpAnim.value = true;
  setTimeout(function() {
    // 简单的粒子模拟
    const colors = ['#FF3B30', '#FF9500', '#FFCC00', '#34C759', '#007AFF', '#5856D6'];
    for (let i = 0; i < 30; i++) {
      const angle = Math.random() * Math.PI * 2;
      const r = Math.random() * 300 + 50;
      const x = Math.cos(angle) * r;
      const y = Math.sin(angle) * r;
      const p = document.createElement('div');
      p.className = 'gsap-particle';
      p.style.backgroundColor = colors[Math.floor(Math.random() * colors.length)];
      p.style.left = '50%';
      p.style.top = '50%';
      document.body.appendChild(p);
      gsap.to(p, {
        x: x, y: y, opacity: 0, duration: 1 + Math.random(), ease: "power2.out",
        onComplete: function() { p.remove(); }
      });
    }
    setTimeout(function() { showLevelUpAnim.value = false; }, 2000);
  }, 100);
}

function handleCardMove(e) {
  const card = e.currentTarget;
  card.style.transform = 'scale(1.005)';
  card.style.boxShadow = '0 8px 24px rgba(0, 122, 255, 0.15)';
  card.style.zIndex = '10';
}
function handleCardLeave(e) {
  const card = e.currentTarget;
  card.style.transform = 'scale(1)';
  card.style.boxShadow = '0 4px 12px rgba(0, 0, 0, 0.05)';
  card.style.zIndex = '1';
}

onMounted(function() {
  loadEnergySystem();
  fetchTodos();
  // 每分钟检查一次超时扣分
  timerInterval = setInterval(checkAutomaticPenalties, 60000);
});

onBeforeUnmount(function() {
  if (timerInterval) clearInterval(timerInterval);
});
</script>

<template>
  <div class="app-container">
    <div class="aurora-bg"></div>

    <!-- 升级动画 -->
    <div v-if="showLevelUpAnim" class="mystery-overlay">
      <div class="mystery-content">
        <div class="mystery-icon">🎉</div>
        <h1>元气值 UP!</h1>
      </div>
    </div>

    <div class="layout-grid">
      <aside class="sidebar">
        <div class="window-controls">
          <span class="dot red"></span><span class="dot yellow"></span><span class="dot green"></span>
        </div>

        <div class="logo">
          <div class="logo-icon"><i class="fas fa-check"></i></div>
          <span>Reminders</span>
        </div>

        <!-- 元气仪表盘 -->
        <div class="energy-widget">
          <div class="energy-top">
            <span class="energy-label">元气值</span>
            <span class="energy-val">{{ energy }}%</span>
          </div>
          <div class="progress-bar">
            <div class="progress-fill" :style="{ width: energy + '%', backgroundColor: energyStatus.color }"></div>
          </div>
          <div class="energy-bottom">
            <span>{{ energyStatus.icon }} {{ energyStatus.text }}</span>
          </div>
        </div>

        <nav class="nav-menu">
          <div class="nav-group">
            <label>SMART LISTS</label>
            <div class="nav-item" :class="{ active: statusFilter === 'all' }" @click="statusFilter = 'all'">
              <div class="icon-wrap gray"><i class="fas fa-inbox"></i></div><span>全部</span><span class="count">{{ totalCount }}</span>
            </div>
            <div class="nav-item" :class="{ active: statusFilter === 'active' }" @click="statusFilter = 'active'">
              <div class="icon-wrap orange"><i class="fas fa-calendar-day"></i></div><span>进行中</span><span class="count">{{ pendingCount }}</span>
            </div>
            <div class="nav-item" :class="{ active: statusFilter === 'completed' }" @click="statusFilter = 'completed'">
              <div class="icon-wrap green"><i class="fas fa-check-circle"></i></div><span>已完成</span><span class="count">{{ completedCount }}</span>
            </div>
          </div>
          <div class="nav-group mt-4">
            <label>MY LISTS</label>
            <div class="nav-item" :class="{ active: categoryFilter === 'All' }" @click="categoryFilter = 'All'">
              <i class="fas fa-layer-group nav-icon"></i><span>全部类别</span>
            </div>
            <div class="nav-item" :class="{ active: categoryFilter === 'Work' }" @click="categoryFilter = 'Work'">
              <i class="fas fa-briefcase nav-icon" style="color: #007AFF"></i><span>工作</span>
            </div>
            <div class="nav-item" :class="{ active: categoryFilter === 'Study' }" @click="categoryFilter = 'Study'">
              <i class="fas fa-book nav-icon" style="color: #FF9500"></i><span>学习</span>
            </div>
            <div class="nav-item" :class="{ active: categoryFilter === 'Life' }" @click="categoryFilter = 'Life'">
              <i class="fas fa-home nav-icon" style="color: #34C759"></i><span>生活</span>
            </div>
          </div>
        </nav>
      </aside>

      <main class="main-content">
        <header class="top-bar">
          <div class="title-area">
            <h1>Tasks</h1>
            <p class="date-today">{{ new Date().toLocaleDateString('zh-CN', { month: 'long', day: 'numeric', weekday: 'long' }) }}</p>
          </div>
          <div class="search-bar">
            <i class="fas fa-search"></i>
            <input v-model="searchQuery" placeholder="搜索任务...">
          </div>
        </header>

        <div class="stats-row">
          <div class="stat-card" @mousemove="handleCardMove" @mouseleave="handleCardLeave">
            <div class="stat-icon blue"><i class="fas fa-inbox"></i></div>
            <div class="stat-number">{{ totalCount }}</div>
            <div class="stat-label">总任务</div>
          </div>
          <div class="stat-card orange" @mousemove="handleCardMove" @mouseleave="handleCardLeave">
            <div class="stat-icon"><i class="fas fa-clock"></i></div>
            <div class="stat-number">{{ pendingCount }}</div>
            <div class="stat-label">待办</div>
          </div>
          <div class="stat-card green" @mousemove="handleCardMove" @mouseleave="handleCardLeave">
            <div class="stat-icon"><i class="fas fa-check-circle"></i></div>
            <div class="stat-number">{{ completedCount }}</div>
            <div class="stat-label">已完成</div>
          </div>
        </div>

        <div class="input-module apple-panel">
          <div class="module-header">新建任务</div>
          <div class="input-form">
            <div class="form-group"><input v-model="newTodoTitle" placeholder="任务标题" class="apple-input title-input" @keyup.enter="addTodo"></div>
            <div class="form-group"><input v-model="newTodoContent" placeholder="备注" class="apple-input" @keyup.enter="addTodo"></div>
            <div class="form-row">
              <div class="form-group col"><label>截止时间</label><input type="datetime-local" v-model="newTodoDeadline" class="apple-input date-picker"></div>
              <div class="form-group col"><label>列表</label><select v-model="newTodoCategory" class="apple-input apple-select"><option v-for="cat in categories" :key="cat" :value="cat">{{ cat }}</option></select></div>
              <div class="form-group col"><label>优先级</label><select v-model="newTodoPriority" class="apple-input apple-select"><option v-for="p in priorities" :key="p.value" :value="p.value">{{ p.label }}</option></select></div>
              <div class="form-group btn-container"><button class="apple-btn" @click="addTodo">添加</button></div>
            </div>
          </div>
        </div>

        <div class="todo-list">
          <div v-if="loading" class="state-text">同步中...</div>
          <div v-else-if="filteredTodos.length === 0" class="state-text">暂无任务</div>

          <div v-for="todo in filteredTodos" :key="todo.id" class="todo-item apple-panel" :class="{ 'is-done': todo.is_completed }" @mousemove="handleCardMove" @mouseleave="handleCardLeave">
            <div class="item-left">
              <div class="checkbox-circle" :class="{ checked: todo.is_completed }" @click="toggleTodo(todo)">
                <i class="fas fa-check" v-if="todo.is_completed"></i>
              </div>
              <div class="item-content">
                <div class="item-header-row">
                  <h4>{{ todo.title }}</h4>
                  <span class="priority-dot" :style="{ backgroundColor: priorities.find(function(p){ return p.value === todo.priority })?.color }" title="优先级"></span>
                </div>
                <p v-if="todo.description">{{ todo.description }}</p>
                <div class="item-meta">
                   <span v-if="todo.deadline && !todo.is_completed" class="meta-tag deadline" :class="{ 'overdue': getCountdown(todo.deadline).overdue }">
                    <i class="far fa-clock"></i> {{ getCountdown(todo.deadline).text }}
                  </span>
                  <span class="meta-tag category">{{ todo.category }}</span>
                  <select class="mini-select" :value="todo.priority" @change="(e) => updateTask(todo, 'priority', parseInt(e.target.value))" @click.stop title="修改优先级">
                    <option v-for="p in priorities" :key="p.value" :value="p.value">P{{ p.value }}</option>
                  </select>
                </div>
              </div>
            </div>
            <div class="item-right"><button class="icon-btn delete" @click.stop="deleteTodo(todo.id)"><i class="far fa-trash-alt"></i></button></div>
          </div>
        </div>
      </main>
    </div>
  </div>
</template>

<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
html, body { width: 100%; height: 100%; overflow: hidden; font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Segoe UI", Roboto, Helvetica, Arial, sans-serif; }
.gsap-particle { position: fixed; width: 10px; height: 10px; border-radius: 50%; pointer-events: none; z-index: 9999; }
</style>

<style scoped>
@import url("https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css");

:root {
  --apple-blue: #007AFF; --apple-red: #FF453A; --apple-green: #34C759; --apple-orange: #FF9F0A; --apple-gray: #8E8E93;
  --apple-panel: rgba(255, 255, 255, 0.75); --text-primary: #1d1d1f; --border-light: rgba(0, 0, 0, 0.05);
}

.app-container { width: 100%; height: 100%; position: fixed; top: 0; left: 0; background: #F2F6FF; }
.aurora-bg {
  position: absolute; top: 0; left: 0; width: 100%; height: 100%;
  background: radial-gradient(circle at 10% 10%, #D0E8FF 0%, transparent 50%), radial-gradient(circle at 90% 90%, #E8E0FF 0%, transparent 50%), radial-gradient(circle at 50% 50%, #FFFFFF 0%, transparent 80%);
  z-index: 0; filter: blur(60px);
}

.mystery-overlay {
  position: fixed; top: 0; left: 0; width: 100%; height: 100%;
  background: rgba(255, 255, 255, 0.8); backdrop-filter: blur(10px);
  display: flex; align-items: center; justify-content: center; z-index: 1000;
  animation: fadeIn 0.3s ease;
}
.mystery-content { text-align: center; transform: scale(1.2); animation: popIn 0.5s; }
.mystery-icon { font-size: 80px; margin-bottom: 20px; display: block; animation: bounce 1s infinite; }
.mystery-content h1 { font-size: 48px; color: #007AFF; margin: 0; }
@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
@keyframes popIn { from { transform: scale(0.5); opacity: 0; } to { transform: scale(1.2); opacity: 1; } }
@keyframes bounce { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(-20px); } }

.layout-grid { position: relative; z-index: 2; display: flex; width: 100%; height: 100%; }
.sidebar {
  width: 260px; height: 100%; background: rgba(255, 255, 255, 0.5);
  backdrop-filter: blur(30px) saturate(150%); border-right: 1px solid rgba(0,0,0,0.05);
  display: flex; flex-direction: column; padding: 20px; flex-shrink: 0;
}

.energy-widget {
  background: rgba(255,255,255,0.6); border-radius: 12px; padding: 15px; margin-bottom: 20px;
  border: 1px solid white; box-shadow: 0 2px 10px rgba(0,0,0,0.02);
}
.energy-top { display: flex; justify-content: space-between; margin-bottom: 8px; font-size: 12px; font-weight: 600; color: #8E8E93; }
.energy-val { color: #333; }
.progress-bar { width: 100%; height: 6px; background: rgba(0,0,0,0.05); border-radius: 3px; overflow: hidden; margin-bottom: 8px; }
.progress-fill { height: 100%; transition: width 0.5s ease, background-color 0.3s; }
.energy-bottom { font-size: 13px; font-weight: 600; color: #333; }

.window-controls { display: flex; gap: 8px; margin-bottom: 20px; }
.dot { width: 12px; height: 12px; border-radius: 50%; }
.red { background: #FF5F56; } .yellow { background: #FFBD2E; } .green { background: #27C93F; }
.logo { display: flex; align-items: center; gap: 10px; font-size: 18px; font-weight: 600; color: #333; margin-bottom: 20px; opacity: 0.9; }
.logo-icon { width: 28px; height: 28px; background: var(--apple-blue); color: white; border-radius: 7px; display: flex; align-items: center; justify-content: center; font-size: 14px; }
.nav-menu { flex: 1; display: flex; flex-direction: column; gap: 20px; overflow-y: auto; }
.nav-group label { display: block; font-size: 11px; font-weight: 600; color: var(--apple-gray); margin-bottom: 5px; padding-left: 10px; }
.mt-4 { margin-top: 20px; }
.nav-item { display: flex; align-items: center; gap: 10px; padding: 8px 10px; margin-bottom: 2px; border-radius: 6px; cursor: pointer; transition: background 0.15s; color: #444; font-size: 14px; font-weight: 500; }
.nav-item:hover { background: rgba(0,0,0,0.05); }
.nav-item.active { background: rgba(0,0,0,0.08); color: #000; }
.icon-wrap { width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 12px; color: white; }
.nav-icon { width: 24px; text-align: center; font-size: 16px; color: var(--apple-gray); }
.icon-wrap.gray { background: var(--apple-gray); } .icon-wrap.orange { background: var(--apple-orange); } .icon-wrap.green { background: var(--apple-green); }
.count { margin-left: auto; color: var(--apple-gray); font-size: 13px; }
.user-profile { margin-top: auto; display: flex; align-items: center; gap: 10px; padding: 10px; border-top: 1px solid var(--border-light); }
.avatar { width: 32px; height: 32px; background: var(--apple-gray); border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 12px; font-weight: bold; color: white; }
.user-details { display: flex; flex-direction: column; }
.name { font-size: 13px; font-weight: 500; }
.role { font-size: 11px; color: var(--apple-gray); }

.main-content { flex: 1; padding: 40px 50px; overflow-y: auto; display: flex; flex-direction: column; gap: 25px; }
.top-bar { margin-bottom: 10px; display: flex; justify-content: space-between; align-items: flex-end; }
.top-bar h1 { font-size: 32px; font-weight: 700; color: var(--apple-blue); margin-bottom: 2px; }
.date-today { font-size: 18px; color: var(--apple-red); font-weight: 500; }
.search-bar { display: flex; align-items: center; gap: 8px; background: rgba(0,0,0,0.05); padding: 6px 10px; border-radius: 8px; width: 200px; }
.search-bar i { color: var(--apple-gray); font-size: 13px; }
.search-bar input { background: transparent; border: none; color: #333; font-size: 13px; width: 100%; outline: none; }

.stats-row { display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; margin-bottom: 10px; }
.stat-card { background: rgba(255, 255, 255, 0.8); border-radius: 12px; padding: 15px; display: flex; flex-direction: column; border: 1px solid white; box-shadow: 0 2px 10px rgba(0,0,0,0.05); backdrop-filter: blur(20px); transition: all 0.2s; height: 100px; justify-content: space-between; }
.stat-icon { font-size: 18px; width: 30px; height: 30px; border-radius: 50%; display: flex; align-items: center; justify-content: center; color: white; }
.stat-card.blue .stat-icon { background: var(--apple-blue); } .stat-card.orange .stat-icon { background: var(--apple-orange); } .stat-card.green .stat-icon { background: var(--apple-green); }
.stat-number { font-size: 28px; font-weight: 700; color: #333; margin-left: auto; margin-top: -30px; }
.stat-label { font-size: 13px; color: var(--apple-gray); font-weight: 600; }

.apple-panel { background: rgba(255, 255, 255, 0.8); border-radius: 12px; border: 1px solid white; backdrop-filter: blur(20px); padding: 20px; box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05); }
.input-module { display: flex; flex-direction: column; gap: 15px; }
.module-header { font-size: 15px; font-weight: 600; color: #333; border-bottom: 1px solid rgba(0,0,0,0.05); padding-bottom: 10px; margin-bottom: 5px; }
.form-group { margin-bottom: 12px; }
.form-row { display: flex; gap: 12px; align-items: flex-end; }
.col { flex: 1; }
.btn-container { width: 100px; }
label { display: block; font-size: 11px; color: var(--apple-gray); margin-bottom: 4px; font-weight: 600; }
.apple-input { width: 100%; background: rgba(0, 0, 0, 0.03); border: 1px solid rgba(0, 0, 0, 0.05); border-radius: 8px; padding: 10px 12px; color: #333; font-size: 14px; outline: none; transition: border 0.2s; }
.apple-input:focus { border-color: var(--apple-blue); background: white; box-shadow: 0 0 0 3px rgba(10,132,255,0.1); }
.title-input { font-weight: 600; font-size: 15px; }
.apple-select { appearance: none; cursor: pointer; }
.apple-btn { width: 100%; height: 38px; background: var(--apple-blue); color: cornflowerblue; border: none; border-radius: 8px; font-size: 13px; font-weight: 600; cursor: pointer; transition: background 0.2s; }
.apple-btn:hover { background: #0062cc; }

.todo-list { display: flex; flex-direction: column; gap: 10px; padding-bottom: 40px; }
.state-text { text-align: center; color: var(--apple-gray); padding: 20px; }
.todo-item { display: flex; align-items: center; justify-content: space-between; padding: 16px; transition: all 0.2s; cursor: default; }
.is-done { opacity: 0.5; }
.is-done h4 { text-decoration: line-through; color: var(--apple-gray); }
.item-left { display: flex; align-items: flex-start; gap: 15px; flex: 1; }
.checkbox-circle { width: 22px; height: 22px; border-radius: 50%; border: 1.5px solid #c7c7cc; display: flex; align-items: center; justify-content: center; cursor: pointer; flex-shrink: 0; margin-top: 2px; }
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
.icon-btn { background: transparent; border: none; color: #c7c7cc; width: 30px; height: 30px; border-radius: 50%; cursor: pointer; transition: color 0.2s; }
.icon-btn:hover { color: var(--apple-red); background: rgba(255, 69, 58, 0.1); }

@media (max-width: 768px) {
  .layout-grid { flex-direction: column; overflow-y: auto; }
  .sidebar { width: 100%; height: auto; padding: 15px; flex-direction: row; align-items: center; justify-content: space-between; }
  .window-controls, .nav-menu, .user-profile, .energy-widget { display: none; }
  .main-content { padding: 20px; }
  .stats-row { grid-template-columns: 1fr; }
  .form-row { flex-direction: column; gap: 10px; }
  .btn-container { width: 100%; }
}
</style>