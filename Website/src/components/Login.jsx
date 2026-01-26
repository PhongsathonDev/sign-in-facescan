// src/components/Login.jsx
import { useState } from 'react'
import { studentList } from '../students'

function Login({ onLogin }) {
    const [inputID, setInputID] = useState('')

    const handleSubmit = (e) => {
        e.preventDefault();
        const student = studentList[inputID];

        if (student) {
            // ส่งข้อมูลกลับไปให้ App.jsx (เดี๋ยว App.jsx จะพาเปลี่ยนหน้าเอง)
            onLogin({ id: inputID, ...student });
        } else {
            alert("❌ ไม่พบรหัสนักศึกษาในระบบ");
        }
    }

    return (
        <div className="login-card">
            <div className="icon-header">🔐</div>
            <h1>ระบบเช็คชื่อนักศึกษา</h1>
            <p>กรุณากรอกรหัสนักศึกษาเพื่อเข้าสู่ระบบ</p>

            <form onSubmit={handleSubmit}>
                <input
                    type="text"
                    placeholder="รหัสนักศึกษา (เช่น 66201280002)"
                    value={inputID}
                    onChange={(e) => setInputID(e.target.value)}
                    className="input-field"
                    autoFocus
                />
                <button type="submit" className="btn-primary">
                    เข้าสู่ระบบ
                </button>
            </form>
        </div>
    )
}

export default Login