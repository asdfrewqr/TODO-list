<script setup>
import {ref, onMounted, computed, watch} from 'vue';
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
const energy = ref(50); // 初始 50
const penalizedTasks = ref(new Set()); // 记录已自动扣分的任务ID，防止重复扣分
const showLevelUpAnim = ref(false); // 控制神秘动画

// 静态配置
const categories = ['Work', 'Study', 'Life'];
const priorities = [
  {value: 1, label: 'Urgent & Important', color: '#FF3B30'},
  {value: 2, label: 'Important', color: '#FF9500'},
  {value: 3, label: 'Urgent', color: '#007AFF'},
  {value: 4, label: 'Normal', color: '#8E8E93'}
];

// --- 2. 核心逻辑 ---

// 初始化读取本地存储
function loadEnergySystem() {
  const savedEnergy = localStorage.getItem('user_energy');
  if (savedEnergy !== null) energy.value = parseInt(savedEnergy);

  const savedPenalized = localStorage.getItem('penalized_tasks');
  if (savedPenalized) {
    penalizedTasks.value = new Set(JSON.parse(savedPenalized));
  }
}

function saveEnergySystem() {
  localStorage.setItem('user_energy', energy.value);
  localStorage.setItem('penalized_tasks', JSON.stringify([...penalizedTasks.value]));
}

// 改变元气值 (核心函数)
function updateEnergy(amount) {
  const oldVal = energy.value;
  let newVal = oldVal + amount;

  // 限制范围 0-100
  if (newVal > 100) newVal = 100;
  if (newVal < 0) newVal = 0;

  energy.value = newVal;
  saveEnergySystem();

  // 触发神秘动画判定：每增加 10 个 (例如 9->14 不触发, 5->10 触发)
  // 逻辑：如果是加分，且 (旧值 // 10) < (新值 // 10)
  if (amount > 0 && Math.floor(oldVal / 10) < Math.floor(newVal / 10)) {
    triggerMysteryAnimation();
  }
}

// 自动检测超时扣分
function checkAutomaticPenalties() {
  todos.value.forEach(todo => {
    // 如果任务未完成，且有截止日期
    if (!todo.is_completed && todo.deadline) {
      const result = getCountdown(todo.deadline);
      // 如果超时，且之前没扣过分
      if (result.overdue && !penalizedTasks.value.has(todo.id)) {
        // 扣分
        updateEnergy(-5);
        // 记录已扣分
        penalizedTasks.value.add(todo.id);
        saveEnergySystem();
        console.log(`Task #${todo.id} overdue! Energy -5`);
      }
    }
  });
}

function fetchTodos() {
  loading.value = true;
  axios.get(API_URL)
      .then(function (res) {
        todos.value = res.data;
        checkAutomaticPenalties(); // 获取数据后立即检查是否有新超时
      })
      .catch(function (err) {
        console.error(err);
      })
      .finally(function () {
        loading.value = false;
      });
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
      .then(function (res) {
        todos.value.push(res.data);
        newTodoTitle.value = '';
        newTodoContent.value = '';
        newTodoDeadline.value = '';
        newTodoCategory.value = 'Life';
        newTodoPriority.value = 4;
      })
      .catch(function (err) {
        alert('Failed to add task');
      });
}

function toggleTodo(todo) {
  const original = todo.is_completed;
  const nextState = !original;

  // 乐观更新
  todo.is_completed = nextState;

  axios.patch(API_URL + '/' + todo.id + '/toggle')
      .then(() => {
        // --- 元气值结算逻辑 ---
        if (nextState === true) {
          // 任务被标记为完成
          const countdown = getCountdown(todo.deadline);

          if (todo.deadline && countdown.overdue) {
            // 超时完成：虽然完成了，但如果之前没扣过分（虽然 checkAutomaticPenalties 会扣，但双保险），这里可以不加分或者扣分
            // 题目要求：超时未完成会自动减少。
            // 这里如果是“超时补救”，我们设定为：不加分，或者加少一点？
            // 题目说：“在任务设定的截止时间前点击完成任务，元气值会增加5个”。
            // 所以超时完成不加分。
            // 如果之前已经自动扣过分了，这里就不再额外惩罚，只是不算加分。
          } else {
            // 准时完成 (或者没有截止日期)
            // 题目：每次在任务设定的截止时间前点击完成任务，元气值会增加5个
            // 如果没有截止日期，为了鼓励，也+5吧
            updateEnergy(5);
          }
        } else {
          // 任务被取消完成 (回滚分数)
          // 如果刚才加了5分，现在要扣回来？
          // 简化处理：取消完成统一扣5分（但这可能导致负反馈），或者不做处理。
          // 为了防止刷分（点完成+5，取消，点完成+5），我们必须回扣。
          // 简单逻辑：取消完成 -5。
          updateEnergy(-5);
        }
      })
      .catch(function (err) {
        todo.is_completed = original;
      });
}

function updateTask(todo, field, value) {
  const original = todo[field];
  todo[field] = value;
  let payload = {};
  payload[field] = value;
  axios.patch(API_URL + '/' + todo.id, payload).catch(function (err) {
    todo[field] = original;
  });
}

function deleteTodo(id) {
  if (typeof window !== 'undefined' && !confirm('Delete this task?')) return;
  axios.delete(API_URL + '/' + id)
      .then(function () {
        todos.value = todos.value.filter(function (t) {
          return t.id !== id;
        });
      })
      .catch(function (err) {
        console.error(err);
      });
}

function getCountdown(deadlineStr) {
  if (!deadlineStr) return null;
  let clean = deadlineStr;
  if (clean.indexOf('Z') === -1 && clean.indexOf('+') === -1) clean += 'Z';
  const diff = new Date(clean) - new Date();
  if (diff < 0) return {overdue: true, text: 'Overdue'};
  const d = Math.floor(diff / 86400000);
  const h = Math.floor((diff % 86400000) / 3600000);
  return {overdue: false, text: d > 0 ? d + 'd ' + h + 'h' : h + 'h left'};
}

// --- 计算属性 ---
const completedCount = computed(function () {
  return todos.value.filter(function (t) {
    return t.is_completed;
  }).length;
});
const pendingCount = computed(function () {
  return todos.value.filter(function (t) {
    return !t.is_completed;
  }).length;
});
const totalCount = computed(function () {
  return todos.value.length;
});

// 元气状态表情
const energyStatus = computed(function () {
  if (energy.value >= 100) return {icon: '🌞', text: 'Radiant', color: '#FFD700'};
  if (energy.value <= 0) return {icon: '💔', text: 'Exhausted', color: '#FF3B30'};
  if (energy.value >= 80) return {icon: '⚡', text: 'High Energy', color: '#30D158'};
  if (energy.value >= 40) return {icon: '✨', text: 'Good', color: '#0A84FF'};
  return {icon: '☁️', text: 'Low Energy', color: '#8E8E93'};
});

const filteredTodos = computed(function () {
  let result = todos.value;
  if (searchQuery.value.trim()) {
    const query = searchQuery.value.toLowerCase();
    result = result.filter(function (t) {
      return t.title.toLowerCase().includes(query);
    });
  }
  if (statusFilter.value === 'active') result = result.filter(function (t) {
    return !t.is_completed;
  });
  else if (statusFilter.value === 'completed') result = result.filter(function (t) {
    return t.is_completed;
  });
  if (categoryFilter.value !== 'All') result = result.filter(function (t) {
    return t.category === categoryFilter.value;
  });
  return result.sort(function (a, b) {
    if (categoryFilter.value === 'All' && a.category !== b.category) return a.category.localeCompare(b.category);
    return a.priority - b.priority;
  });
});

// --- 交互特效 ---
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

function triggerMysteryAnimation() {
  showLevelUpAnim.value = true;

  // 使用 GSAP 创建全屏爆炸效果
  setTimeout(function () {
    const tl = gsap.timeline();

    // 简单的粒子爆发模拟
    const colors = ['#FF3B30', '#FF9500', '#FFCC00', '#4CD964', '#5AC8FA', '#007AFF', '#5856D6', '#FF2D55'];

    for (let i = 0; i < 50; i++) {
      const angle = Math.random() * Math.PI * 2;
      const radius = Math.random() * 500 + 100;
      const x = Math.cos(angle) * radius;
      const y = Math.sin(angle) * radius;

      // 创建临时 DOM 元素做动画
      const particle = document.createElement('div');
      particle.className = 'gsap-particle';
      particle.style.backgroundColor = colors[Math.floor(Math.random() * colors.length)];
      particle.style.left = '50%';
      particle.style.top = '50%';
      document.body.appendChild(particle);

      gsap.to(particle, {
        x: x,
        y: y,
        opacity: 0,
        duration: 1 + Math.random(),
        ease: "power4.out",
        onComplete: function () {
          particle.remove();
        }
      });
    }

    setTimeout(function () {
      showLevelUpAnim.value = false;
    }, 2000);
  }, 100);
}

onMounted(function () {
  loadEnergySystem();
  fetchTodos();
  // 启动定时器每分钟检查一次超时
  setInterval(checkAutomaticPenalties, 60000);
});
</script>

<template>
  <div class="app-container">
    <!-- 极光背景 -->
    <div class="aurora-bg"></div>

    <!-- 神秘动画覆盖层 -->
    <div v-if="showLevelUpAnim" class="mystery-overlay">
      <div class="mystery-content">
        <div class="mystery-icon">🎉</div>
        <h1>ENERGY SURGE!</h1>
        <p>You are unstoppable!</p>
      </div>
    </div>

    <div class="layout-grid">
      <!-- 侧边栏 -->
      <aside class="sidebar">
        <div class="window-controls">
          <span class="dot red"></span><span class="dot yellow"></span><span class="dot green"></span>
        </div>

        <!-- 元气值仪表盘 (新增) -->
        <div class="energy-dashboard">
          <div class="energy-header">
            <span class="energy-label">VITALITY</span>
            <span class="energy-score">{{ energy }}%</span>
          </div>
          <div class="energy-bar-track">
            <div class="energy-bar-fill" :style="{ width: energy + '%', backgroundColor: energyStatus.color }"></div>
          </div>
          <div class="energy-status">
            <span class="status-emoji">{{ energyStatus.icon }}</span>
            <span class="status-text" :style="{ color: energyStatus.color }">{{ energyStatus.text }}</span>
          </div>
        </div>

        <nav class="nav-menu">
          <!-- 菜单项保持不变 -->
          <div class="nav-group">
            <label>SMART LISTS</label>
            <div class="nav-item" :class="{ active: statusFilter === 'all' }" @click="statusFilter = 'all'">
              <div class="icon-wrap gray"><i class="fas fa-inbox"></i></div>
              <span>All</span><span class="count">{{ totalCount }}</span>
            </div>
            <div class="nav-item" :class="{ active: statusFilter === 'active' }" @click="statusFilter = 'active'">
              <div class="icon-wrap orange"><i class="fas fa-calendar-day"></i></div>
              <span>Scheduled</span><span class="count">{{ pendingCount }}</span>
            </div>
            <div class="nav-item" :class="{ active: statusFilter === 'completed' }" @click="statusFilter = 'completed'">
              <div class="icon-wrap green"><i class="fas fa-check-circle"></i></div>
              <span>Done</span><span class="count">{{ completedCount }}</span>
            </div>
          </div>
          <div class="nav-group mt-4">
            <label>LISTS</label>
            <div class="nav-item" :class="{ active: categoryFilter === 'All' }" @click="categoryFilter = 'All'">
              <i class="fas fa-layer-group nav-icon"></i><span>All Categories</span>
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
            <p class="date-today">{{
                new Date().toLocaleDateString('en-US', {
                  weekday: 'long',
                  month: 'long',
                  day: 'numeric'
                })
              }}</p>
          </div>
          <div class="search-bar">
            <i class="fas fa-search"></i>
            <input v-model="searchQuery" placeholder="Search">
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
            <div class="form-group"><input v-model="newTodoTitle" placeholder="Title" class="apple-input title-input"
                                           @keyup.enter="addTodo"></div>
            <div class="form-group"><input v-model="newTodoContent" placeholder="Notes" class="apple-input"
                                           @keyup.enter="addTodo"></div>
            <div class="form-row">
              <div class="form-group col"><label>Date</label><input type="datetime-local" v-model="newTodoDeadline"
                                                                    class="apple-input date-picker"></div>
              <div class="form-group col"><label>List</label><select v-model="newTodoCategory"
                                                                     class="apple-input apple-select">
                <option v-for="cat in categories" :key="cat" :value="cat">{{ cat }}</option>
              </select></div>
              <div class="form-group col"><label>Priority</label><select v-model="newTodoPriority"
                                                                         class="apple-input apple-select">
                <option v-for="p in priorities" :key="p.value" :value="p.value">{{ p.label }}</option>
              </select></div>
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

          <div v-for="todo in filteredTodos" :key="todo.id" class="todo-item apple-panel"
               :class="{ 'is-done': todo.is_completed }" @mousemove="handleCardMove" @mouseleave="handleCardLeave">
            <div class="item-left">
              <div class="checkbox-circle" :class="{ checked: todo.is_completed }" @click="toggleTodo(todo)">
                <i class="fas fa-check" v-if="todo.is_completed"></i>
              </div>
              <div class="item-content">
                <div class="item-header-row">
                  <h4>{{ todo.title }}</h4>
                  <span class="priority-dot"
                        :style="{ backgroundColor: priorities.find(function(p){ return p.value === todo.priority })?.color }"
                        title="Priority"></span>
                </div>
                <p v-if="todo.description">{{ todo.description }}</p>
                <div class="item-meta">
                   <span v-if="todo.deadline && !todo.is_completed" class="meta-tag deadline"
                         :class="{ 'overdue': getCountdown(todo.deadline).overdue }">
                    {{ getCountdown(todo.deadline).text }}
                  </span>
                  <span class="meta-tag category">{{ todo.category }}</span>
                  <select class="mini-select" :value="todo.priority"
                          @change="(e) => updateTask(todo, 'priority', parseInt(e.target.value))" @click.stop
                          title="Change Priority">
                    <option v-for="p in priorities" :key="p.value" :value="p.value">P{{ p.value }}</option>
                  </select>
                </div>
              </div>
            </div>
            <div class="item-right">
              <button class="icon-btn delete" @click.stop="deleteTodo(todo.id)"><i class="far fa-trash-alt"></i>
              </button>
            </div>
          </div>
        </div>
      </main>
    </div>
  </div>
</template>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html, body {
  width: 100%;
  height: 100%;
  overflow: hidden;
  font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
}

/* GSAP 粒子样式 */
.gsap-particle {
  position: fixed;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  pointer-events: none;
  z-index: 9999;
}
</style>

<style scoped>
@import url("https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css");

:root {
  --apple-blue: #007AFF;
  --apple-red: #FF453A;
  --apple-green: #34C759;
  --apple-orange: #FF9F0A;
  --apple-gray: #8E8E93;
  --apple-panel: rgba(255, 255, 255, 0.75);
  --text-primary: #1d1d1f;
  --border-light: rgba(0, 0, 0, 0.05);
}

.app-container {
  width: 100%;
  height: 100%;
  position: fixed;
  top: 0;
  left: 0;
  background: #F2F6FF;
}

.aurora-bg {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: radial-gradient(circle at 10% 10%, #D0E8FF 0%, transparent 50%), radial-gradient(circle at 90% 90%, #E8E0FF 0%, transparent 50%), radial-gradient(circle at 50% 50%, #FFFFFF 0%, transparent 80%);
  z-index: 0;
  filter: blur(60px);
}

/* 神秘动画覆盖层 */
.mystery-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(10px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  animation: fadeIn 0.3s ease;
}

.mystery-content {
  text-align: center;
  transform: scale(1.2);
  animation: popIn 0.5s cubic-bezier(0.175, 0.885, 0.32, 1.275);
}

.mystery-icon {
  font-size: 80px;
  margin-bottom: 20px;
  display: block;
  animation: bounce 1s infinite;
}

.mystery-content h1 {
  font-size: 48px;
  color: #007AFF;
  margin: 0;
  text-transform: uppercase;
  letter-spacing: 2px;
}

.mystery-content p {
  font-size: 24px;
  color: #8E8E93;
  margin-top: 10px;
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

@keyframes popIn {
  from {
    transform: scale(0.5);
    opacity: 0;
  }
  to {
    transform: scale(1.2);
    opacity: 1;
  }
}

@keyframes bounce {
  0%, 100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-20px);
  }
}

.layout-grid {
  position: relative;
  z-index: 2;
  display: flex;
  width: 100%;
  height: 100%;
}

.sidebar {
  width: 280px;
  height: 100%;
  background: rgba(255, 255, 255, 0.5);
  backdrop-filter: blur(30px) saturate(150%);
  border-right: 1px solid rgba(0, 0, 0, 0.05);
  display: flex;
  flex-direction: column;
  padding: 20px;
  flex-shrink: 0;
}

/* 元气仪表盘样式 */
.energy-dashboard {
  background: rgba(255, 255, 255, 0.6);
  border-radius: 12px;
  padding: 15px;
  border: 1px solid rgba(255, 255, 255, 0.8);
  margin-bottom: 20px;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
}

.energy-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
  font-size: 12px;
  font-weight: 700;
  color: #8E8E93;
}

.energy-score {
  color: #1d1d1f;
}

.energy-bar-track {
  width: 100%;
  height: 8px;
  background: rgba(0, 0, 0, 0.05);
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 10px;
}

.energy-bar-fill {
  height: 100%;
  transition: width 0.5s cubic-bezier(0.4, 0, 0.2, 1), background-color 0.3s;
}

.energy-status {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  font-size: 14px;
}

.status-emoji {
  font-size: 20px;
}

.window-controls {
  display: flex;
  gap: 8px;
  margin-bottom: 20px;
}

.dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
}

.red {
  background: #FF5F56;
}

.yellow {
  background: #FFBD2E;
}

.green {
  background: #27C93F;
}

.logo {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 18px;
  font-weight: 600;
  color: #333;
  margin-bottom: 20px;
  opacity: 0.9;
}

.logo-icon {
  width: 28px;
  height: 28px;
  background: var(--apple-blue);
  color: white;
  border-radius: 7px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
}

.nav-menu {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 20px;
  overflow-y: auto;
}

.nav-group label {
  display: block;
  font-size: 11px;
  font-weight: 600;
  color: var(--apple-gray);
  margin-bottom: 5px;
  padding-left: 10px;
}

.mt-4 {
  margin-top: 20px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 10px;
  margin-bottom: 2px;
  border-radius: 6px;
  cursor: pointer;
  transition: background 0.15s;
  color: #444;
  font-size: 14px;
  font-weight: 500;
}

.nav-item:hover {
  background: rgba(0, 0, 0, 0.05);
}

.nav-item.active {
  background: rgba(0, 0, 0, 0.08);
  color: #000;
}

.icon-wrap {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  color: white;
}

.nav-icon {
  width: 24px;
  text-align: center;
  font-size: 16px;
  color: var(--apple-gray);
}

.icon-wrap.gray {
  background: var(--apple-gray);
}

.icon-wrap.orange {
  background: var(--apple-orange);
}

.icon-wrap.green {
  background: var(--apple-green);
}

.count {
  margin-left: auto;
  color: var(--apple-gray);
  font-size: 13px;
}

.user-profile {
  margin-top: auto;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px;
  border-top: 1px solid var(--border-light);
}

.avatar {
  width: 32px;
  height: 32px;
  background: var(--apple-gray);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: bold;
  color: white;
}

.user-details {
  display: flex;
  flex-direction: column;
}

.name {
  font-size: 13px;
  font-weight: 500;
}

.role {
  font-size: 11px;
  color: var(--apple-gray);
}

.main-content {
  flex: 1;
  padding: 40px 50px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 25px;
}

.top-bar {
  margin-bottom: 10px;
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
}

.top-bar h1 {
  font-size: 32px;
  font-weight: 700;
  color: var(--apple-blue);
  margin-bottom: 2px;
}

.date-today {
  font-size: 18px;
  color: var(--apple-red);
  font-weight: 500;
}

.search-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  background: rgba(0, 0, 0, 0.05);
  padding: 6px 10px;
  border-radius: 8px;
  width: 200px;
}

.search-bar i {
  color: var(--apple-gray);
  font-size: 13px;
}

.search-bar input {
  background: transparent;
  border: none;
  color: #333;
  font-size: 13px;
  width: 100%;
  outline: none;
}

.stats-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 15px;
  margin-bottom: 10px;
}

.stat-card {
  background: rgba(255, 255, 255, 0.8);
  border-radius: 12px;
  padding: 15px;
  display: flex;
  flex-direction: column;
  border: 1px solid white;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
  backdrop-filter: blur(20px);
  transition: all 0.2s;
  height: 100px;
  justify-content: space-between;
}

.stat-icon {
  font-size: 18px;
  width: 30px;
  height: 30px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

.stat-card.blue .stat-icon {
  background: var(--apple-blue);
}

.stat-card.orange .stat-icon {
  background: var(--apple-orange);
}

.stat-card.green .stat-icon {
  background: var(--apple-green);
}

.stat-number {
  font-size: 28px;
  font-weight: 700;
  color: #333;
  margin-left: auto;
  margin-top: -30px;
}

.stat-label {
  font-size: 13px;
  color: var(--apple-gray);
  font-weight: 600;
}

.apple-panel {
  background: rgba(255, 255, 255, 0.8);
  border-radius: 12px;
  border: 1px solid white;
  backdrop-filter: blur(20px);
  padding: 20px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05);
}

.input-module {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.module-header {
  font-size: 15px;
  font-weight: 600;
  color: #333;
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
  padding-bottom: 10px;
  margin-bottom: 5px;
}

.form-group {
  margin-bottom: 12px;
}

.form-row {
  display: flex;
  gap: 12px;
  align-items: flex-end;
}

.col {
  flex: 1;
}

.btn-container {
  width: 100px;
}

label {
  display: block;
  font-size: 11px;
  color: var(--apple-gray);
  margin-bottom: 4px;
  font-weight: 600;
}

.apple-input {
  width: 100%;
  background: rgba(0, 0, 0, 0.03);
  border: 1px solid rgba(0, 0, 0, 0.05);
  border-radius: 8px;
  padding: 10px 12px;
  color: #333;
  font-size: 14px;
  outline: none;
  transition: border 0.2s;
}

.apple-input:focus {
  border-color: var(--apple-blue);
  background: white;
  box-shadow: 0 0 0 3px rgba(10, 132, 255, 0.1);
}

.title-input {
  font-weight: 600;
  font-size: 15px;
}

.apple-select {
  appearance: none;
  cursor: pointer;
}

.apple-btn {
  width: 100%;
  height: 38px;
  background: var(--apple-blue);
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
}

.apple-btn:hover {
  background: #0062cc;
}

.todo-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding-bottom: 40px;
}

.state-text {
  text-align: center;
  color: var(--apple-gray);
  padding: 20px;
}

.todo-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px;
  transition: all 0.2s;
  cursor: default;
}

.is-done {
  opacity: 0.5;
}

.is-done h4 {
  text-decoration: line-through;
  color: var(--apple-gray);
}

.item-left {
  display: flex;
  align-items: flex-start;
  gap: 15px;
  flex: 1;
}

.checkbox-circle {
  width: 22px;
  height: 22px;
  border-radius: 50%;
  border: 1.5px solid #c7c7cc;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  flex-shrink: 0;
  margin-top: 2px;
}

.checkbox-circle.checked {
  background: var(--apple-blue);
  border-color: var(--apple-blue);
  color: white;
  font-size: 12px;
}

.item-content {
  flex: 1;
}

.item-header-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 2px;
}

.priority-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  display: inline-block;
}

.item-content h4 {
  font-size: 15px;
  font-weight: 500;
  margin: 0;
}

.item-content p {
  font-size: 13px;
  color: var(--apple-gray);
  line-height: 1.4;
  margin-bottom: 4px;
}

.item-meta {
  display: flex;
  gap: 8px;
  align-items: center;
  flex-wrap: wrap;
}

.meta-tag {
  font-size: 10px;
  padding: 2px 6px;
  border-radius: 4px;
  font-weight: 600;
  letter-spacing: 0.3px;
  text-transform: uppercase;
}

.deadline-tag {
  color: var(--apple-blue);
  background: rgba(10, 132, 255, 0.1);
}

.deadline-tag.overdue {
  color: var(--apple-red);
  background: rgba(255, 69, 58, 0.1);
}

.category {
  color: #8E8E93;
  background: rgba(0, 0, 0, 0.05);
}

.mini-select {
  border: none;
  background: transparent;
  font-size: 10px;
  color: #888;
  cursor: pointer;
}

.icon-btn {
  background: transparent;
  border: none;
  color: #c7c7cc;
  width: 30px;
  height: 30px;
  border-radius: 50%;
  cursor: pointer;
  transition: color 0.2s;
}

.icon-btn:hover {
  color: var(--apple-red);
  background: rgba(255, 69, 58, 0.1);
}

@media (max-width: 768px) {
  .layout-grid {
    flex-direction: column;
    overflow-y: auto;
  }

  .sidebar {
    width: 100%;
    height: auto;
    padding: 15px;
    flex-direction: row;
    align-items: center;
    justify-content: space-between;
  }

  .window-controls, .nav-menu, .user-profile {
    display: none;
  }

  .main-content {
    padding: 20px;
  }

  .stats-row {
    grid-template-columns: 1fr;
  }

  .form-row {
    flex-direction: column;
    gap: 10px;
  }

  .btn-container {
    width: 100%;
  }
}
</style>