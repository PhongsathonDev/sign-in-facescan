// src/components/Dashboard.jsx
import { useState, useEffect } from 'react'
import { db } from '../firebase' // ถอยกลับไป 1 โฟลเดอร์
import { ref, onValue } from 'firebase/database'

function Dashboard({ user, onLogout }) {
    const [attendanceData, setAttendanceData] = useState([])
    const [loading, setLoading] = useState(false)

    useEffect(() => {
        if (!user) return;

        setLoading(true);
        const dbRef = ref(db, 'attendance');

        onValue(dbRef, (snapshot) => {
            const data = snapshot.val();
            if (data) {
                const loadedData = [];

                Object.keys(data).forEach(dateKey => {
                    const studentsInDate = data[dateKey];
                    // กรองเอาเฉพาะข้อมูลของ User ที่ล็อกอินเข้ามา
                    if (studentsInDate[user.id]) {
                        const studentData = studentsInDate[user.id];
                        loadedData.push({
                            date: dateKey,
                            id: user.id,
                            name: studentData.name,
                            class: studentData.class,
                            time: studentData.time
                        });
                    }
                });

                setAttendanceData(loadedData.reverse());
            } else {
                setAttendanceData([]);
            }
            setLoading(false);
        });
    }, [user])

    return (
        <div className="dashboard-container">
            <header className="dashboard-header">
                <div>
                    <h2>สวัสดี, {user.name} 👋</h2>
                    <span className="badge">{user.class}</span>
                </div>
                <button onClick={onLogout} className="btn-secondary">
                    ออกจากระบบ
                </button>
            </header>

            <div className="content-area">
                <h3>ประวัติการเข้าเรียน 📋</h3>

                {loading ? <p>กำลังโหลดข้อมูล...</p> : (
                    attendanceData.length === 0 ? (
                        <div className="empty-state">ไม่พบประวัติการเข้าเรียน</div>
                    ) : (
                        <div className="table-responsive">
                            <table className="purple-table">
                                <thead>
                                    <tr>
                                        <th>วันที่</th>
                                        <th>เวลาที่สแกน</th>
                                        <th>สถานะ</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {attendanceData.map((item, index) => (
                                        <tr key={index}>
                                            <td>{item.date}</td>
                                            <td style={{ fontWeight: 'bold' }}>{item.time}</td>
                                            <td><span className="status-ok">เช็คชื่อสำเร็จ</span></td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    )
                )}
            </div>
        </div>
    )
}

export default Dashboard