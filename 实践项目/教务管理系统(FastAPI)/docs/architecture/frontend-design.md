# 前端路由架构与状态管理设计

## 1. 路由架构

### 1.1 路由设计原则
- 动态路由：登录后根据角色加载不同菜单
- 路由守卫：未登录跳转登录页，越权访问提示 403
- 懒加载：所有页面组件按需加载

### 1.2 路由表

```javascript
// 静态路由（无需权限）
const constantRoutes = [
  { path: '/login', name: 'Login', component: () => import('@/views/login/index.vue') },
  { path: '/403', name: '403', component: () => import('@/views/error/403.vue') },
  { path: '/404', name: '404', component: () => import('@/views/error/404.vue') },
]

// 动态路由（按角色加载）
const asyncRoutes = [
  {
    path: '/',
    component: Layout,
    redirect: '/dashboard',
    children: [
      { path: 'dashboard', name: 'Dashboard', meta: { title: '仪表盘', icon: 'HomeFilled', roles: ['admin','academic_staff','teacher','student'] } },
    ]
  },
  // 系统管理（仅admin）
  {
    path: '/system',
    component: Layout,
    meta: { title: '系统管理', icon: 'Setting', roles: ['admin'] },
    children: [
      { path: 'users', name: 'Users', meta: { title: '用户管理' } },
      { path: 'roles', name: 'Roles', meta: { title: '角色管理' } },
    ]
  },
  // 学院专业（admin, academic_staff）
  {
    path: '/college',
    component: Layout,
    meta: { title: '基础数据', icon: 'School', roles: ['admin','academic_staff'] },
    children: [
      { path: 'colleges', name: 'Colleges', meta: { title: '学院管理' } },
      { path: 'majors', name: 'Majors', meta: { title: '专业管理' } },
      { path: 'classes', name: 'Classes', meta: { title: '班级管理' } },
      { path: 'classrooms', name: 'Classrooms', meta: { title: '教室管理' } },
      { path: 'semesters', name: 'Semesters', meta: { title: '学期管理' } },
    ]
  },
  // 教师管理（admin, academic_staff）
  {
    path: '/teacher',
    component: Layout,
    meta: { title: '教师管理', icon: 'UserFilled', roles: ['admin','academic_staff'] },
    children: [
      { path: 'list', name: 'TeacherList', meta: { title: '教师列表' } },
    ]
  },
  // 学生管理（admin, academic_staff）
  {
    path: '/student',
    component: Layout,
    meta: { title: '学生管理', icon: 'User', roles: ['admin','academic_staff'] },
    children: [
      { path: 'list', name: 'StudentList', meta: { title: '学生列表' } },
    ]
  },
  // 课程管理（admin, academic_staff）
  {
    path: '/course',
    component: Layout,
    meta: { title: '课程管理', icon: 'Reading', roles: ['admin','academic_staff'] },
    children: [
      { path: 'list', name: 'CourseList', meta: { title: '课程列表' } },
    ]
  },
  // 排课管理（admin, academic_staff）
  {
    path: '/schedule',
    component: Layout,
    meta: { title: '排课管理', icon: 'Calendar', roles: ['admin','academic_staff'] },
    children: [
      { path: 'list', name: 'ScheduleList', meta: { title: '排课列表' } },
    ]
  },
  // 选课管理（admin, academic_staff）+ 学生选课（student）
  {
    path: '/selection',
    component: Layout,
    meta: { title: '选课管理', icon: 'List', roles: ['admin','academic_staff','student'] },
    children: [
      { path: 'stats', name: 'SelectionStats', meta: { title: '选课统计', roles: ['admin','academic_staff'] } },
      { path: 'available', name: 'SelectionAvailable', meta: { title: '可选课程', roles: ['student'] } },
      { path: 'my', name: 'SelectionMy', meta: { title: '我的课程', roles: ['student'] } },
    ]
  },
  // 课表（所有角色）
  {
    path: '/timetable',
    component: Layout,
    meta: { title: '课表查看', icon: 'Tickets', roles: ['admin','academic_staff','teacher','student'] },
    children: [
      { path: 'view', name: 'TimetableView', meta: { title: '课表' } },
    ]
  },
  // 点名（admin, academic_staff, teacher）
  {
    path: '/attendance',
    component: Layout,
    meta: { title: '点名管理', icon: 'Checked', roles: ['admin','academic_staff','teacher'] },
    children: [
      { path: 'mark', name: 'AttendanceMark', meta: { title: '点名', roles: ['teacher'] } },
      { path: 'records', name: 'AttendanceRecords', meta: { title: '出勤记录' } },
      { path: 'stats', name: 'AttendanceStats', meta: { title: '考勤统计' } },
    ]
  },
  // 成绩
  {
    path: '/score',
    component: Layout,
    meta: { title: '成绩管理', icon: 'DataAnalysis', roles: ['admin','academic_staff','teacher','student'] },
    children: [
      { path: 'input', name: 'ScoreInput', meta: { title: '成绩录入', roles: ['teacher'] } },
      { path: 'query', name: 'ScoreQuery', meta: { title: '成绩查询', roles: ['admin','academic_staff','teacher'] } },
      { path: 'my', name: 'ScoreMy', meta: { title: '我的成绩', roles: ['student'] } },
    ]
  },
  // 作业
  {
    path: '/assignment',
    component: Layout,
    meta: { title: '作业管理', icon: 'Document', roles: ['admin','academic_staff','teacher','student'] },
    children: [
      { path: 'manage', name: 'AssignmentManage', meta: { title: '作业管理', roles: ['teacher'] } },
      { path: 'list', name: 'AssignmentList', meta: { title: '作业列表', roles: ['student'] } },
    ]
  },
  // 请假（P1）
  { /* ... */ },
  // 预警（P1）
  { /* ... */ },
  // 社团（P1）
  { /* ... */ },
  // 公告（P1）
  { /* ... */ },
]
```

### 1.3 路由守卫逻辑
```
router.beforeEach((to, from, next) => {
  // 1. 白名单路由直接放行（login, 404, 403）
  // 2. 未登录 → 跳转 login
  // 3. 已登录 + 访问 login → 重定向 dashboard
  // 4. 已登录 → 检查路由 meta.roles 是否包含当前角色
  //    包含 → 放行
  //    不包含 → 跳转 403
})
```

---

## 2. 状态管理（Pinia）

### 2.1 Store 设计

```
store/
├── user.js          // 用户状态
│   ├── state: { token, userInfo, roles, permissions }
│   ├── actions: { login(), logout(), fetchUserInfo() }
│   └── getters: { isLoggedIn, currentRole }
│
├── app.js           // 应用状态
│   ├── state: { sidebarCollapsed, currentSemester }
│   └── actions: { toggleSidebar(), setSemester() }
│
└── modules/         // 业务模块状态
    ├── timetable.js   // 课表数据缓存
    ├── selection.js   // 选课状态（可选列表、已选列表）
    └── notification.js // 通知/公告
```

### 2.2 Axios 封装

```javascript
// api/request.js
const service = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  timeout: 15000,
})

// 请求拦截器
service.interceptors.request.use(config => {
  const token = useUserStore().token
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// 响应拦截器
service.interceptors.response.use(
  response => {
    const { code, message } = response.data
    if (code === 200) return response.data
    ElMessage.error(message || '请求失败')
    return Promise.reject(new Error(message))
  },
  error => {
    if (error.response?.status === 401) {
      useUserStore().logout()
      router.push('/login')
    }
    ElMessage.error(error.message || '网络错误')
    return Promise.reject(error)
  }
)
```

---

## 3. 布局架构

```
Layout.vue
├── Sidebar (侧边栏)
│   ├── Logo
│   └── Menu (根据角色动态渲染)
│       ├── 仪表盘 (所有角色)
│       ├── 系统管理 (admin)
│       ├── 基础数据 (admin, staff)
│       ├── 教师管理 (admin, staff)
│       ├── 学生管理 (admin, staff)
│       ├── 课程管理 (admin, staff)
│       ├── 排课管理 (admin, staff)
│       ├── 选课管理 (admin, staff, student)
│       ├── 课表查看 (所有)
│       ├── 点名管理 (admin, staff, teacher)
│       ├── 成绩管理 (所有)
│       ├── 作业管理 (所有)
│       └── ...
├── Navbar (顶部导航)
│   ├── Breadcrumb (面包屑)
│   ├── 当前学期选择器
│   ├── 通知图标
│   └── 用户下拉 (个人信息/修改密码/退出)
└── Main Content (主内容区)
    └── <router-view />
```
