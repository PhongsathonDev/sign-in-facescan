import { useState, useEffect } from 'react'
import { db } from './firebase'
import { ref, onValue } from 'firebase/database'
import './App.css'

function App() {
  const [attendanceData, setAttendanceData] = useState([])

  useEffect(() => {
    // เปลี่ยนจาก 'students' เป็น 'attendance' ให้ตรงกับในรูป
    const dbRef = ref(db, 'attendance');

    onValue(dbRef, (snapshot) => {
      const data = snapshot.val();
      if (data) {
        const loadedData = [];

        // Loop ชั้นที่ 1: ดึง "วันที่" (เช่น 2026-01-14)
        Object.keys(data).forEach(dateKey => {
          const studentsInDate = data[dateKey];

          // Loop ชั้นที่ 2: ดึง "รหัสนักศึกษา" ในวันที่นั้นๆ
          Object.keys(studentsInDate).forEach(studentId => {
            const student = studentsInDate[studentId];

            // เก็บข้อมูลรวมกันไว้ใน Array เดียว
            loadedData.push({
              date: dateKey,      // วันที่
              id: studentId,      // รหัสนักศึกษา (key)
              name: student.name, // ชื่อ
              class: student.class, // ห้อง
              time: student.time  // เวลา
            });
          });
        });

        // กลับด้านข้อมูล (ให้ข้อมูลล่าสุดขึ้นก่อน) และอัปเดต State
        setAttendanceData(loadedData.reverse());
      } else {
        setAttendanceData([]);
      }
    });
  }, [])

  return (
    <div style={{ maxWidth: '800px', margin: '0 auto', padding: '20px', fontFamily: 'Sarabun, sans-serif' }}>
      <h1 style={{ textAlign: 'center' }}>ระบบเช็คชื่อนักศึกษา 📋</h1>

      {attendanceData.length === 0 ? (
        <p style={{ textAlign: 'center' }}>...กำลังโหลด หรือ ไม่มีข้อมูล...</p>
      ) : (
        <table style={{ width: '100%', borderCollapse: 'collapse', marginTop: '20px' }}>
          <thead>
            <tr style={{ backgroundColor: '#f2f2f2', textAlign: 'left' }}>
              <th style={thStyle}>วันที่</th>
              <th style={thStyle}>เวลา</th>
              <th style={thStyle}>รหัสนักศึกษา</th>
              <th style={thStyle}>ชื่อ-นามสกุล</th>
              <th style={thStyle}>ห้อง</th>
            </tr>
          </thead>
          <tbody>
            {attendanceData.map((item, index) => (
              <tr key={index} style={{ borderBottom: '1px solid #ddd' }}>
                <td style={tdStyle}>{item.date}</td>
                <td style={tdStyle}>{item.time}</td>
                <td style={tdStyle}>{item.id}</td>
                <td style={tdStyle}>{item.name}</td>
                <td style={tdStyle}>{item.class}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  )
}

// สไตล์ตกแต่งตารางเล็กน้อย
const thStyle = { padding: '12px', borderBottom: '2px solid #ddd' };
const tdStyle = { padding: '10px' };

export default App