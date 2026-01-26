import { useState, useEffect } from 'react'
import { Routes, Route, Navigate, useNavigate } from 'react-router-dom'
import Login from './components/Login'
import Dashboard from './components/Dashboard'
import './App.css'

function App() {
  const [currentUser, setCurrentUser] = useState(null)
  const [loadingSession, setLoadingSession] = useState(true)
  const navigate = useNavigate() // ตัวช่วยเปลี่ยนหน้า

  // 1. ตรวจสอบ Session เมื่อเปิดเว็บ
  useEffect(() => {
    const savedUser = localStorage.getItem('attendanceAppUser');
    if (savedUser) {
      setCurrentUser(JSON.parse(savedUser));
    }
    setLoadingSession(false);
  }, [])

  // 2. ฟังก์ชัน Login (บันทึก -> ไปหน้า home)
  const handleLogin = (userData) => {
    setCurrentUser(userData);
    localStorage.setItem('attendanceAppUser', JSON.stringify(userData));
    navigate('/home'); // สั่งให้เปลี่ยนหน้าไป home
  }

  // 3. ฟังก์ชัน Logout (ลบ -> กลับหน้า login)
  const handleLogout = () => {
    setCurrentUser(null);
    localStorage.removeItem('attendanceAppUser');
    navigate('/login'); // สั่งให้กลับหน้า login
  }

  // Loading...
  if (loadingSession) {
    return <div style={{ color: 'white', textAlign: 'center', marginTop: '50px' }}>Loading...</div>;
  }

  // --- ส่วนจัดการเส้นทาง (Router) ---
  return (
    <div className="app-container">
      <Routes>
        {/* หน้า Login: ถ้าล็อกอินอยู่แล้ว ให้ดีดไป home เลย */}
        <Route
          path="/login"
          element={
            !currentUser ? (
              <Login onLogin={handleLogin} />
            ) : (
              <Navigate to="/home" replace />
            )
          }
        />

        {/* หน้า Home: ถ้ายังไม่ล็อกอิน ให้ดีดไป login (Protected Route) */}
        <Route
          path="/home"
          element={
            currentUser ? (
              <Dashboard user={currentUser} onLogout={handleLogout} />
            ) : (
              <Navigate to="/login" replace />
            )
          }
        />

        {/* ถ้าพิมพ์มั่วๆ หรือเข้าหน้าแรก (/) ให้เช็คว่าล็อกอินยัง? */}
        <Route
          path="*"
          element={<Navigate to={currentUser ? "/home" : "/login"} replace />}
        />
      </Routes>
    </div>
  )
}

export default App