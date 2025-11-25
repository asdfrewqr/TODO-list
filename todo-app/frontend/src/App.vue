<script setup>
import { ref, onMounted, onBeforeUnmount, computed } from 'vue';
import axios from 'axios';
import gsap from 'gsap';

// --- 1. 状态管理 ---
const todos = ref([]);
const newTodoTitle = ref('');
const newTodoContent = ref('');
const newTodoDeadline = ref('');
const loading = ref(false);
const filter = ref('all');
const API_URL = 'http://127.0.0.1:8000/todos';

// --- 2. 核心逻辑 (Promise 链式调用) ---

function fetchTodos() {
  loading.value = true;
  axios.get(API_URL)
    .then(function(response) {
      todos.value = response.data;
    })
    .catch(function(error) {
      console.error(error);
    })
    .finally(function() {
      loading.value = false;
    });
}

function addTodo() {
  if (!newTodoTitle.value.trim()) return;

  // 处理日期格式
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
  .then(function(response) {
    todos.value.push(response.data);
    newTodoTitle.value = '';
    newTodoContent.value = '';
    newTodoDeadline.value = '';
  })
  .catch(function(error) {
    if (typeof window !== 'undefined') alert('Mission failed: Add task error');
  });
}

function toggleTodo(todo) {
  const original = todo.is_completed;
  todo.is_completed = !todo.is_completed;

  axios.patch(`${API_URL}/${todo.id}/toggle`)
    .catch(function(error) {
      todo.is_completed = original;
    });
}

function deleteTodo(id) {
  if (typeof window !== 'undefined' && !confirm('Terminate this protocol?')) return;

  axios.delete(`${API_URL}/${id}`)
    .then(function() {
      todos.value = todos.value.filter(function(t) { return t.id !== id; });
    })
    .catch(function(error) {
      console.error(error);
    });
}

// 倒计时逻辑
function getCountdown(deadlineStr) {
  if (!deadlineStr) return null;

  let cleanDeadline = deadlineStr;
  if (!cleanDeadline.endsWith('Z') && !cleanDeadline.includes('+')) {
      cleanDeadline += 'Z';
  }

  const now = new Date();
  const deadline = new Date(cleanDeadline);
  const diff = deadline - now;

  if (diff < 0) return { overdue: true, text: '⚠️ TIMEOUT' };

  const days = Math.floor(diff / (1000 * 60 * 60 * 24));
  const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
  const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));

  let text = '';
  if (days > 0) text += `${days}d `;
  text += `${hours}h ${minutes}m`;

  return { overdue: false, text: text };
}

// 统计数据
const completedCount = computed(function() { return todos.value.filter(function(t) { return t.is_completed; }).length; });
const pendingCount = computed(function() { return todos.value.filter(function(t) { return !t.is_completed; }).length; });
const totalCount = computed(function() { return todos.value.length; });

const filteredTodos = computed(function() {
  if (filter.value === 'active') return todos.value.filter(function(t) { return !t.is_completed; });
  if (filter.value === 'completed') return todos.value.filter(function(t) { return t.is_completed; });
  return todos.value;
});

// --- 3. 交互特效 ---

function handleCardMove(e) {
  const card = e.currentTarget;
  const rect = card.getBoundingClientRect();
  const x = e.clientX - rect.left;
  const y = e.clientY - rect.top;

  const rotateY = (x / rect.width - 0.5) * 5;
  const rotateX = (y / rect.height - 0.5) * -5;

  card.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) scale(1.01)`;

  if (card.classList.contains('card-overdue')) {
    card.style.borderColor = '#ff3333';
    card.style.boxShadow = '0 0 25px rgba(255, 51, 51, 0.4)';
  } else {
    card.style.borderColor = 'var(--neon-cyan)';
    card.style.boxShadow = '0 0 20px rgba(0, 243, 255, 0.3)';
  }
  card.style.zIndex = '10';
}

function handleCardLeave(e) {
  const card = e.currentTarget;
  card.style.transform = 'perspective(1000px) rotateX(0) rotateY(0) scale(1)';

  if (card.classList.contains('card-overdue')) {
    card.style.borderColor = 'rgba(255, 51, 51, 0.5)';
    card.style.boxShadow = 'none';
  } else {
    card.style.borderColor = 'rgba(255, 255, 255, 0.15)';
    card.style.boxShadow = '0 4px 15px rgba(0, 0, 0, 0.2)';
  }
  card.style.zIndex = '1';
}

function handleMenuEnter(e) {
  const item = e.currentTarget;
  const oldHighlight = item.querySelector('.highlight');
  if (oldHighlight) oldHighlight.remove();

  const highlight = document.createElement('div');
  highlight.classList.add('highlight');

  const rect = item.getBoundingClientRect();
  const x = e.clientX - rect.left;
  const y = e.clientY - rect.top;

  highlight.style.left = '0';
  highlight.style.top = '0';
  highlight.style.width = '100%';
  highlight.style.height = '100%';
  highlight.style.background = `radial-gradient(circle at ${x}px ${y}px, rgba(188, 19, 254, 0.25) 0%, rgba(0, 0, 0, 0) 60%)`;

  item.appendChild(highlight);

  setTimeout(function() {
    highlight.style.opacity = '0';
    setTimeout(function() { if (highlight.parentNode) highlight.remove(); }, 300);
  }, 500);
}

// --- 4. GSAP 粒子背景逻辑 ---
let ctx, ctx2, cw, ch, xTo, yTo;
const m = { x: 0, y: 0 };
const arr = [];
const arr2 = [];
const T = Math.PI * 2;

function initBackground() {
  const c = document.querySelector("#c");
  const c2 = document.querySelector("#c2");
  if (!c || !c2) return;

  ctx = c.getContext("2d");
  ctx2 = c2.getContext("2d");

  function resizeCanvas() {
    cw = c.width = window.innerWidth;
    ch = c.height = window.innerHeight;
    c2.width = window.innerWidth;
    c2.height = window.innerHeight;
  }
  resizeCanvas();
  window.addEventListener('resize', resizeCanvas);

  m.x = cw / 2; m.y = 0;

  xTo = gsap.quickTo(m, "x", { duration: 1.5, ease: "expo" });
  yTo = gsap.quickTo(m, "y", { duration: 1.5, ease: "expo" });

  window.addEventListener('pointermove', function(e) {
    xTo(e.clientX);
    yTo(e.clientY);
  });

  for (let i = 0; i < 600; i++) {
    const item = {
      i: i, cx: cw / 2, cy: gsap.utils.mapRange(0, 600, 600, 3700, i),
      r: (i < 500) ? gsap.utils.mapRange(0, 600, 3, 770, i) : 50,
      dot: 9, prog: 0.25, s: 1
    };
    arr.push(item);
    const d = 99;
    item.t = gsap.timeline({ repeat: -1 })
      .to(item, { duration: d, prog: "+=1", ease: "slow(0.3, 0.4)" })
      .to(item, { duration: d / 2, s: 0.15, repeat: 1, yoyo: true, ease: "power3.inOut" }, 0)
      .seek(Math.random() * d);

    const item2 = { x: cw * Math.random(), y: -10, s: 2 + 5 * Math.random(), a: 0.5 + 0.5 * Math.random() };
    arr2.push(item2);
    item2.t = gsap.timeline({ repeat: -1 }).to(item2, { duration: 66, ease: 'none', y: ch }).seek(Math.random() * d).timeScale(item2.s / 11);
  }
  gsap.ticker.add(render);
  gsap.from(arr, { duration: 1, dot: 0, ease: 'back.out(9)', stagger: -0.0009 });
}

function render() {
  if (!ctx || !ctx2) return;
  ctx.clearRect(0, 0, cw, ch);
  ctx2.clearRect(0, 0, cw, ch);
  ctx.fillStyle = "#fff";
  ctx.strokeStyle = "rgba(255,255,255,0.1)";
  ctx.globalCompositeOperation = "lighter";
  arr.forEach(function(c) {
    const angle = c.prog * T;
    const x = Math.cos(angle) * c.r + c.cx;
    const y = (Math.sin(angle) * c.r) * 0.2 + c.cy;
    const d = Math.sqrt((x - m.x) ** 2 + (y - m.y) ** 2);
    const ms = gsap.utils.clamp(0.07, 1, d / cw);
    ctx.beginPath(); ctx.arc(x, y, c.dot * c.s / 2 / ms, 0, T); ctx.fill(); ctx.lineWidth = c.dot * c.s * 2 / ms; ctx.stroke();
  });
  arr2.forEach(function(c) {
    const ys = gsap.utils.interpolate(1.3, 0.1, c.y / ch);
    ctx2.beginPath();
    ctx2.arc(c.x, c.y, c.s * ys, 0, T);
    ctx2.globalAlpha = c.a * ys;
    ctx2.fill();
  });
}

onMounted(function () {
  fetchTodos();
  initBackground();
});

onBeforeUnmount(function () {
  gsap.ticker.remove(render);
  arr.forEach(function (i) {
    if (i.t) i.t.kill()
  });
  arr2.forEach(function (i) {
    if (i.t) i.t.kill()
  });
});
</script>

<template>
  <div class="app-wrapper">
    <div id="fixed-bg">
      <canvas id="c2"></canvas>
      <canvas id="c"></canvas>
    </div>

    <div class="layout-center">
      <div class="glass-container">

        <!-- 侧边栏 -->
        <aside class="sidebar">
          <div class="logo">
            <i class="fab fa-react brands-icon"></i>
          </div>
          <nav class="menu">
            <ul>
              <li :class="{ active: filter === 'all' }" @click="filter = 'all'" @mouseenter="handleMenuEnter">
                <a href="#">
                  <i class="fas fa-globe"></i>
                  <span>Center</span>
                </a>
              </li>
              <li :class="{ active: filter === 'active' }" @click="filter = 'active'" @mouseenter="handleMenuEnter">
                <a href="#">
                  <i class="fas fa-satellite-dish"></i>
                  <span>Pending</span>
                </a>
              </li>
              <li :class="{ active: filter === 'completed' }" @click="filter = 'completed'"
                  @mouseenter="handleMenuEnter">
                <a href="#">
                  <i class="fas fa-check-double"></i>
                  <span>Logs</span>
                </a>
              </li>
              <li @mouseenter="handleMenuEnter">
                <a href="#"><i class="fas fa-chart-pie"></i><span>Data</span></a>
              </li>
            </ul>
          </nav>

          <div class="profile">
            <div class="avatar">
              <img src="https://api.dicebear.com/9.x/bottts-neutral/svg?seed=Felix" alt="User">
            </div>
            <div class="user-info">
              <h3>Commander</h3>
              <p>Level 99</p>
            </div>
          </div>
        </aside>

        <!-- 主内容区 -->
        <main class="content">
          <header>
            <h1>Command Center</h1>
            <p>System Status: <span class="neon-text">ONLINE</span></p>
          </header>

          <!-- 统计卡片 -->
          <div class="card-container">
            <div class="card stat-card grad-green" @mousemove="handleCardMove" @mouseleave="handleCardLeave">
              <div class="card-icon">
                <i class="fas fa-check"></i>
              </div>
              <div class="card-info">
                <h3>{{ completedCount }}</h3>
                <p>Completed</p>
              </div>
            </div>
            <div class="card stat-card grad-orange" @mousemove="handleCardMove" @mouseleave="handleCardLeave">
              <div class="card-icon">
                <i class="fas fa-clock"></i>
              </div>
              <div class="card-info">
                <h3>{{ pendingCount }}</h3>
                <p>Pending</p>
              </div>
            </div>
            <div class="card stat-card grad-purple" @mousemove="handleCardMove" @mouseleave="handleCardLeave">
              <div class="card-icon">
                <i class="fas fa-layer-group"></i>
              </div>
              <div class="card-info">
                <h3>{{ totalCount }}</h3>
                <p>Total Ops</p>
              </div>
            </div>
          </div>

          <!-- 任务输入区 -->
          <div class="input-section">
            <div class="glass-input-group">
              <div class="inputs">
                <input
                    v-model="newTodoTitle"
                    @keyup.enter="addTodo"
                    placeholder="New Protocol Title..."
                    class="glass-input title-input"
                />
                <div class="input-row">
                  <input
                      v-model="newTodoContent"
                      @keyup.enter="addTodo"
                      placeholder="Parameters (Optional)..."
                      class="glass-input desc-input"
                  />
                  <!-- 美化后的日期选择器 -->
                  <input
                      type="datetime-local"
                      v-model="newTodoDeadline"
                      class="glass-input date-input"
                  />
                </div>
              </div>
              <button @click="addTodo" class="deploy-btn">
                <i class="fas fa-plus"></i>
              </button>
            </div>
          </div>

          <!-- 任务列表 -->
          <div class="todo-grid">
            <div v-if="loading" class="loading-text">Scanning...</div>
            <div v-else-if="filteredTodos.length === 0" class="empty-text">No signals detected.</div>

            <div
                v-for="todo in filteredTodos"
                :key="todo.id"
                class="card todo-card"
                :class="{
                'card-done': todo.is_completed,
                'card-overdue': !todo.is_completed && getCountdown(todo.deadline)?.overdue
              }"
                @mousemove="handleCardMove"
                @mouseleave="handleCardLeave"
            >
              <div class="todo-header">
                <span class="todo-id">ID-{{ todo.id }}</span>
                <button class="delete-btn" @click.stop="deleteTodo(todo.id)">
                  <i class="fas fa-times"></i>
                </button>
              </div>

              <div class="todo-body" @click="toggleTodo(todo)">
                <h4>{{ todo.title }}</h4>
                <p>{{ todo.description || 'No details provided.' }}</p>
              </div>

              <div class="todo-footer">
                <div class="status-row">
                  <div class="status-pill" :class="todo.is_completed ? 'st-green' : 'st-yellow'">
                    {{ todo.is_completed ? 'DONE' : 'ACTIVE' }}
                  </div>

                  <!-- 倒计时显示 -->
                  <div v-if="todo.deadline && !todo.is_completed"
                       class="deadline-pill"
                       :class="{ 'overdue': getCountdown(todo.deadline).overdue }">
                    <i class="fas fa-stopwatch"></i>
                    {{ getCountdown(todo.deadline).text }}
                  </div>
                </div>
              </div>
            </div>
          </div>

        </main>
      </div>
    </div>
  </div>
</template>

<style>
/* --- 全局样式重置 --- */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html, body {
  width: 100%;
  height: 100%;
  overflow: hidden;
  background: #000;
  margin: 0;
}

::-webkit-scrollbar {
  width: 8px;
}

::-webkit-scrollbar-track {
  background: rgba(255, 255, 255, 0.05);
}

::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.3);
  border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.5);
}
</style>

<style scoped>
@import url("https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css");
@import url('https://fonts.googleapis.com/css2?family=Rajdhani:wght@400;600;700&display=swap');

:root {
  --neon-cyan: #00f3ff;
  --neon-purple: #bc13fe;
  --neon-green: #0aff0a;
  --text-main: #ffffff;
  --text-muted: #e0e0e0;
}

.app-wrapper {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: #000;
  font-family: 'Rajdhani', sans-serif;
  color: var(--text-main);
}

#fixed-bg {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 0;
  pointer-events: none;
}

canvas {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
}

/* --- 布局核心：左上角对齐，容器撑满 --- */
.layout-center {
  position: relative;
  z-index: 10;
  display: flex;
  width: 100%;
  height: 100%;
  padding: 0;
}

.glass-container {
  display: flex;
  width: 100%;
  height: 100%;

  /* 玻璃拟态核心 - 提高不透明度 */
  background: rgba(35, 40, 60, 0.85);
  backdrop-filter: blur(40px);
  -webkit-backdrop-filter: blur(40px);

  border: 1px solid rgba(255, 255, 255, 0.25);
  box-shadow: 0 0 60px rgba(0, 0, 0, 0.8);
  overflow: hidden;
  border-radius: 0;
}

/* --- 侧边栏 --- */
.sidebar {
  width: 280px;
  height: 100%;
  padding: 30px 20px;
  background: rgba(20, 22, 40, 0.6);
  border-right: 1px solid rgba(255, 255, 255, 0.15);
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
}

.logo {
  text-align: center;
  margin-bottom: 40px;
}

.brands-icon {
  font-size: 42px;
  color: var(--neon-cyan);
  filter: drop-shadow(0 0 15px rgba(0, 243, 255, 0.8));
}

.menu ul {
  list-style: none;
  padding: 0;
  margin: 0;
}

.menu li {
  margin-bottom: 10px;
  border-radius: 12px;
  position: relative;
  overflow: hidden;
  transition: all 0.3s;
}

.menu li:hover {
  background: rgba(255, 255, 255, 0.1);
}

.menu li.active {
  background: linear-gradient(90deg, rgba(188, 19, 254, 0.25), transparent);
  border-left: 4px solid var(--neon-purple);
}

.menu a {
  display: flex;
  align-items: center;
  color: #d1d5db;
  padding: 14px 16px;
  text-decoration: none;
  font-weight: 600;
  letter-spacing: 1px;
  transition: color 0.3s;
}

.menu li.active a {
  color: #fff;
  text-shadow: 0 0 8px rgba(188, 19, 254, 0.8);
}

.menu a i {
  width: 24px;
  margin-right: 12px;
  text-align: center;
  font-size: 18px;
}

.profile {
  margin-top: auto;
  display: flex;
  align-items: center;
  padding: 15px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  border: 1px solid rgba(255, 255, 255, 0.15);
}

.avatar img {
  width: 40px;
  height: 40px;
  border-radius: 8px;
  border: 2px solid var(--neon-cyan);
}

.user-info {
  margin-left: 12px;
}

.user-info h3 {
  font-size: 15px;
  margin: 0;
  font-weight: 700;
  color: #fff;
}

.user-info p {
  font-size: 12px;
  color: var(--neon-cyan);
  margin: 0;
  font-weight: 600;
}

/* --- 主内容区 --- */
.content {
  flex: 1;
  padding: 40px 50px;
  overflow-y: auto;
  overflow-x: hidden;
  display: flex;
  flex-direction: column;
  background: radial-gradient(circle at top right, rgba(0, 243, 255, 0.08), transparent 50%),
  radial-gradient(circle at bottom left, rgba(188, 19, 254, 0.08), transparent 50%);
}

header {
  margin-bottom: 30px;
}

header h1 {
  font-size: 38px;
  margin-bottom: 5px;
  font-weight: 800;
  color: #fff;
  letter-spacing: 1px;
  text-shadow: 0 2px 15px rgba(0, 0, 0, 0.5);
}

header p {
  color: #ddd;
  font-size: 16px;
}

.neon-text {
  color: var(--neon-green);
  text-shadow: 0 0 15px rgba(10, 255, 10, 0.8);
  font-weight: bold;
}

/* --- 统计卡片 --- */
.card-container {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 25px;
  margin-bottom: 40px;
}

.card {
  background: rgba(45, 50, 75, 0.8);
  backdrop-filter: blur(20px);
  border-radius: 20px;
  padding: 25px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  transition: transform 0.1s, box-shadow 0.2s;
  position: relative;
  overflow: hidden;
}

.grad-green {
  background: linear-gradient(135deg, rgba(16, 185, 129, 0.4), rgba(45, 50, 75, 0.9));
  border: 1px solid rgba(16, 185, 129, 0.5);
}

.grad-orange {
  background: linear-gradient(135deg, rgba(245, 158, 11, 0.4), rgba(45, 50, 75, 0.9));
  border: 1px solid rgba(245, 158, 11, 0.5);
}

.grad-purple {
  background: linear-gradient(135deg, rgba(139, 92, 246, 0.4), rgba(45, 50, 75, 0.9));
  border: 1px solid rgba(139, 92, 246, 0.5);
}

.stat-card {
  display: flex;
  align-items: center;
}

.card-icon {
  width: 56px;
  height: 56px;
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 20px;
  font-size: 26px;
  background: rgba(255, 255, 255, 0.2);
  color: #fff;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
}

.card-info h3 {
  font-size: 36px;
  margin: 0;
  font-weight: 700;
  color: #fff;
  line-height: 1.1;
}

.card-info p {
  font-size: 14px;
  color: #eee;
  margin: 0;
  font-weight: 600;
  letter-spacing: 1px;
}

/* --- 输入框 --- */
.input-section {
  margin-bottom: 40px;
}

.glass-input-group {
  display: flex;
  align-items: center;
  background: rgba(255, 255, 255, 0.12);
  border: 1px solid rgba(255, 255, 255, 0.25);
  border-radius: 16px;
  padding: 15px 25px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.25);
}

.inputs {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.input-row {
  display: flex;
  gap: 10px;
  width: 100%;
}

.glass-input {
  background: transparent;
  border: none;
  color: #fff;
  outline: none;
  font-family: 'Rajdhani', sans-serif;
}

.title-input {
  font-size: 20px;
  font-weight: 700;
  color: #fff;
  width: 100%;
}

.desc-input {
  font-size: 15px;
  color: #e5e7eb;
  flex: 1;
}

.glass-input::placeholder {
  color: #bbb;
}

/* 美化后的日期选择器 */
.date-input {
  color: #ffffff;
  font-family: 'Rajdhani', sans-serif;
  font-size: 14px;
  background: rgba(10, 15, 30, 0.8); /* 深色背景，确保对比度 */
  border: 1px solid rgba(0, 243, 255, 0.3); /* 青色微光边框 */
  border-radius: 8px;
  padding: 0 12px;
  height: 100%; /* 填满高度 */
  color-scheme: dark; /* 强制浏览器使用深色原生控件 */
  transition: all 0.3s ease;
  min-width: 200px;
  letter-spacing: 1px;
}

.date-input:focus {
  border-color: var(--neon-cyan);
  box-shadow: 0 0 15px rgba(0, 243, 255, 0.3);
  background: rgba(10, 15, 30, 1);
}

/* 定制日历图标颜色 */
.date-input::-webkit-calendar-picker-indicator {
  filter: invert(1) drop-shadow(0 0 3px var(--neon-cyan));
  cursor: pointer;
  opacity: 0.8;
}

.date-input::-webkit-calendar-picker-indicator:hover {
  opacity: 1;
  transform: scale(1.1);
}

.deploy-btn {
  background: linear-gradient(135deg, #00f3ff, #0066ff);
  color: #fff;
  border: none;
  border-radius: 12px;
  width: 55px;
  height: 55px;
  font-size: 24px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
  box-shadow: 0 0 20px rgba(0, 243, 255, 0.4);
}

.deploy-btn:hover {
  transform: scale(1.05);
  box-shadow: 0 0 30px rgba(0, 243, 255, 0.7);
}

/* --- 任务列表 --- */
.todo-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 25px;
  padding-bottom: 30px;
}

.todo-card {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  min-height: 180px;
  cursor: pointer;
}

.todo-card:hover {
  border-color: var(--neon-cyan);
}

/* 超时卡片红色警告 */
.card-overdue {
  border-color: rgba(255, 51, 51, 0.6) !important;
  box-shadow: 0 0 15px rgba(255, 51, 51, 0.2);
}

.card-overdue .todo-header {
  color: #ff3333;
}

.card-done {
  opacity: 0.8;
  filter: grayscale(0.6);
  border-color: var(--neon-green);
}

.card-done .todo-body {
  text-decoration: line-through;
  color: #ccc;
}

.todo-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 15px;
  font-size: 14px;
  color: var(--neon-cyan);
  font-weight: 600;
}

.delete-btn {
  background: transparent;
  border: none;
  color: #ff6b6b;
  cursor: pointer;
  font-size: 18px;
  opacity: 0.9;
  transition: all 0.2s;
}

.delete-btn:hover {
  opacity: 1;
  transform: scale(1.2);
  text-shadow: 0 0 15px #ff0000;
}

.todo-body h4 {
  font-size: 22px;
  margin: 0 0 8px 0;
  color: #fff;
  font-weight: 700;
  line-height: 1.3;
}

.todo-body p {
  font-size: 15px;
  color: #e5e7eb;
  margin: 0;
  line-height: 1.5;
}

.todo-footer {
  margin-top: 20px;
  padding-top: 15px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  font-size: 13px;
}

.status-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.status-pill {
  display: inline-block;
  padding: 4px 10px;
  border-radius: 6px;
  font-weight: bold;
  font-size: 12px;
  letter-spacing: 1px;
}

.st-green {
  background: rgba(16, 185, 129, 0.2);
  color: #34d399;
  border: 1px solid rgba(16, 185, 129, 0.3);
  box-shadow: 0 0 10px rgba(16, 185, 129, 0.2);
}

.st-yellow {
  background: rgba(245, 158, 11, 0.2);
  color: #fbbf24;
  border: 1px solid rgba(245, 158, 11, 0.3);
  box-shadow: 0 0 10px rgba(245, 158, 11, 0.2);
}

.deadline-pill {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 12px;
  font-weight: bold;
  color: var(--neon-cyan);
  background: rgba(0, 243, 255, 0.1);
  padding: 4px 8px;
  border-radius: 4px;
}

.deadline-pill.overdue {
  color: #ff3333;
  background: rgba(255, 51, 51, 0.15);
  border: 1px solid rgba(255, 51, 51, 0.3);
  animation: pulse-red 2s infinite;
}

@keyframes pulse-red {
  0% {
    box-shadow: 0 0 0 0 rgba(255, 51, 51, 0.4);
  }
  70% {
    box-shadow: 0 0 0 6px rgba(255, 51, 51, 0);
  }
  100% {
    box-shadow: 0 0 0 0 rgba(255, 51, 51, 0);
  }
}

@media (max-width: 768px) {
  .glass-container {
    flex-direction: column;
    height: 100vh;
  }

  .sidebar {
    width: 100%;
    height: auto;
    flex-direction: row;
    align-items: center;
    justify-content: space-between;
    padding: 15px;
    border-right: none;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  }

  .menu ul {
    display: flex;
    gap: 15px;
  }

  .menu span, .profile {
    display: none;
  }

  .content {
    padding: 20px;
  }

  .todo-grid {
    grid-template-columns: 1fr;
  }

  .input-row {
    flex-direction: column;
  }

  .date-input {
    width: 100%;
    margin-top: 10px;
  }
}
</style>