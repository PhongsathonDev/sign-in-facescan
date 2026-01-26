import { useState, useEffect } from 'react'
import { db } from '../firebase'
import { ref, onValue } from 'firebase/database'

function Dashboard({ user, onLogout }) {
    const [attendanceData, setAttendanceData] = useState([])
    const [loading, setLoading] = useState(false)

    // ดึงข้อมูลจาก Firebase
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
                            time: studentData.time,
                            status: "Present" // สมมติว่าถ้ามีข้อมูลคือมาเรียน
                        });
                    }
                });
                // เรียงลำดับจากวันที่ล่าสุด
                setAttendanceData(loadedData.reverse());
            } else {
                setAttendanceData([]);
            }
            setLoading(false);
        });
    }, [user])

    // คำนวณสถิติ
    const totalPresent = attendanceData.length;
    // สมมติเป้าหมาย 20 วัน (แก้ได้ตามจริง)
    const attendancePercentage = Math.min(Math.round((totalPresent / 20) * 100), 100);

    return (
        <div className="bg-background-light dark:bg-background-dark text-[#140d1b] dark:text-white font-display min-h-screen transition-colors duration-200">

            {/* --- Header --- */}
            <header className="sticky top-0 z-40 flex items-center justify-between border-b border-[#ede7f3] bg-white/80 dark:bg-[#1e1429]/80 backdrop-blur-md px-6 py-4 lg:px-10">
                <div className="flex items-center gap-4">
                    <div className="flex size-10 items-center justify-center rounded-xl bg-primary/10 text-primary">
                        <span className="material-symbols-outlined text-3xl">L</span>
                    </div>
                    <h2 className="text-xl font-bold tracking-tight text-[#140d1b] dark:text-white">วิทยาลัยเทคนิคอำนาจเจริญ</h2>
                </div>

                <div className="flex items-center gap-4 sm:gap-6">
                    <div className="hidden text-right sm:block">
                        <p className="text-sm font-bold leading-none text-[#140d1b] dark:text-white">{user.name}</p>
                        <p className="text-xs text-[#734c9a] dark:text-[#a58cc5]">ID: {user.id}</p>
                    </div>
                    {/* Avatar Placeholder */}
                    <div className="flex items-center justify-center size-10 rounded-full bg-primary text-white font-bold ring-2 ring-white shadow-sm">
                        {user.name.charAt(0)}
                    </div>

                    <button
                        onClick={onLogout}
                        className="flex items-center justify-center rounded-lg bg-[#ede7f3] hover:bg-red-100 text-[#140d1b] hover:text-red-600 p-2 transition-colors"
                        title="ออกจากระบบ"
                    >
                        <span className="material-symbols-outlined">logout</span>
                    </button>
                </div>
            </header>

            {/* --- Main Content --- */}
            <main className="px-4 py-8 sm:px-6 lg:px-8">
                <div className="mx-auto max-w-[1100px] space-y-8">

                    {/* Page Heading */}
                    <div className="flex flex-wrap items-end justify-between gap-4">
                        <div className="flex flex-col gap-1">
                            <h1 className="text-3xl font-black tracking-tight text-[#140d1b] dark:text-black sm:text-4xl">
                                แดชบอร์ดการเข้าเรียน
                            </h1>
                            <p className="text-[#734c9a] dark:text-[#a58cc5] font-medium">ภาคเรียนที่ 1/2569</p>
                        </div>
                        <div className="flex items-center gap-2 rounded-full bg-white dark:bg-[#1e1429] px-4 py-1.5 text-sm font-medium shadow-sm border border-[#ede7f3]">
                            <span className="relative flex h-2.5 w-2.5">
                                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                                <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-green-500"></span>
                            </span>
                            <span>สถานะ: ปกติ</span>
                        </div>
                    </div>

                    {/* --- Stats Cards --- */}
                    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">

                        {/* Card 1: Overall Attendance */}
                        <div className="relative flex flex-col justify-between overflow-hidden rounded-2xl border border-[#dbcfe7] bg-white p-6 shadow-sm hover:-translate-y-1 transition-transform">
                            <div className="flex items-start justify-between">
                                <div>
                                    <p className="text-sm font-medium text-[#734c9a]">การเข้าเรียนรวม</p>
                                    <p className="mt-2 text-5xl font-bold tracking-tight text-primary text-[#734c9a]">{attendancePercentage}%</p>
                                </div>
                                <div className="flex size-12 items-center justify-center rounded-full bg-primary/10 text-primary">
                                    <span className="material-symbols-outlined">donut_large</span>
                                </div>
                            </div>
                            <div className="mt-4 h-1.5 w-full rounded-full bg-[#f0ebf5]">
                                <div className="h-1.5 rounded-full bg-primary" style={{ width: `${attendancePercentage}%` }}></div>
                            </div>
                            <p className="mt-2 text-xs text-gray-500">เป้าหมายขั้นต่ำ: 80%</p>
                        </div>

                        {/* Card 2: Status */}
                        <div className="relative flex flex-col justify-between rounded-2xl border border-[#dbcfe7] bg-white p-6 shadow-sm hover:-translate-y-1 transition-transform">
                            <div className="flex items-start justify-between">
                                <p className="text-sm font-medium text-[#734c9a]">สถานะนักศึกษา</p>
                                <span className="material-symbols-outlined text-green-600">verified_user</span>
                            </div>
                            <div className="mt-2 flex items-center gap-3">
                                <span className="inline-flex items-center rounded-lg bg-green-50 px-3 py-1 text-lg font-bold text-green-700 ring-1 ring-inset ring-green-600/20">
                                    ผ่าน
                                </span>
                            </div>
                            <p className="mt-4 text-sm text-gray-600">
                                คุณมีสิทธิ์เข้าสอบปลายภาคในรายวิชาที่ลงทะเบียนทั้งหมด
                            </p>
                        </div>

                        {/* Card 3: Summary Stats */}
                        <div className="relative flex flex-col justify-between rounded-2xl border border-[#dbcfe7] bg-white p-6 shadow-sm hover:-translate-y-1 transition-transform">
                            <p className="text-sm font-medium text-[#734c9a] mb-4">สรุปสถิติ</p>
                            <div className="flex flex-1 items-end gap-2">
                                <div className="flex flex-1 flex-col items-center gap-1 rounded-xl bg-green-50 p-2 text-center border border-green-100">
                                    <span className="text-2xl font-bold text-green-700">{totalPresent}</span>
                                    <span className="text-[10px] uppercase font-bold text-green-600/70">มาเรียน</span>
                                </div>
                                <div className="flex flex-1 flex-col items-center gap-1 rounded-xl bg-yellow-50 p-2 text-center border border-yellow-100">
                                    <span className="text-2xl font-bold text-yellow-700">0</span>
                                    <span className="text-[10px] uppercase font-bold text-yellow-600/70">สาย</span>
                                </div>
                                <div className="flex flex-1 flex-col items-center gap-1 rounded-xl bg-red-50 p-2 text-center border border-red-100">
                                    <span className="text-2xl font-bold text-red-700">0</span>
                                    <span className="text-[10px] uppercase font-bold text-red-600/70">ขาด</span>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* --- Table --- */}
                    <div className="rounded-2xl border border-[#dbcfe7] bg-white shadow-sm overflow-hidden">
                        <div className="border-b border-[#ede7f3] px-6 py-4 flex justify-between items-center">
                            <h3 className="text-lg font-bold text-[#140d1b]">ประวัติการเช็คชื่อ</h3>
                            <button className="flex items-center gap-1 text-sm font-medium text-primary hover:text-primary-dark">
                                <span className="material-symbols-outlined text-lg">filter_list</span>
                                ตัวกรอง
                            </button>
                        </div>

                        <div className="overflow-x-auto">
                            {loading ? (
                                <div className="p-8 text-center text-gray-500">กำลังโหลดข้อมูล...</div>
                            ) : attendanceData.length === 0 ? (
                                <div className="p-8 text-center text-gray-500">ไม่พบข้อมูลการเข้าเรียน</div>
                            ) : (
                                <table className="w-full text-left text-sm">
                                    <thead className="bg-[#faf8fc]">
                                        <tr>
                                            <th className="whitespace-nowrap px-6 py-4 font-semibold text-[#140d1b]">วันที่</th>
                                            <th className="whitespace-nowrap px-6 py-4 font-semibold text-[#140d1b]">กิจกรรม/วิชา</th>
                                            <th className="whitespace-nowrap px-6 py-4 font-semibold text-[#140d1b]">สถานะ</th>
                                            <th className="whitespace-nowrap px-6 py-4 font-semibold text-[#140d1b]">เวลาที่สแกน</th>
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y divide-[#ede7f3]">
                                        {attendanceData.map((item, index) => (
                                            <tr key={index} className="hover:bg-gray-50 transition-colors">
                                                <td className="whitespace-nowrap px-6 py-4 text-[#734c9a] font-medium">{item.date}</td>
                                                <td className="whitespace-nowrap px-6 py-4 text-[#140d1b]">เช็คชื่อเข้าแถว/โฮมรูม</td>
                                                <td className="whitespace-nowrap px-6 py-4">
                                                    <span className="inline-flex items-center gap-1.5 rounded-full bg-green-50 px-2.5 py-1 text-xs font-bold text-green-700 ring-1 ring-inset ring-green-600/20">
                                                        <span className="size-1.5 rounded-full bg-green-500"></span>
                                                        มาเรียน
                                                    </span>
                                                </td>
                                                <td className="whitespace-nowrap px-6 py-4 text-[#734c9a] font-mono">{item.time}</td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            )}
                        </div>

                        {/* Pagination Footer (Mock) */}
                        <div className="flex items-center justify-between border-t border-[#ede7f3] px-6 py-4">
                            <p className="text-sm text-[#734c9a]">แสดง <span className="font-bold text-[#140d1b]">1-{attendanceData.length}</span> รายการ</p>
                            <div className="flex gap-2">
                                <button className="rounded-lg border border-[#dbcfe7] px-3 py-1.5 text-sm font-medium text-[#140d1b] hover:bg-gray-50 disabled:opacity-50" disabled>ก่อนหน้า</button>
                                <button className="rounded-lg border border-[#dbcfe7] px-3 py-1.5 text-sm font-medium text-[#140d1b] hover:bg-gray-50 disabled:opacity-50" disabled>ถัดไป</button>
                            </div>
                        </div>
                    </div>

                </div>
            </main>



        </div>
    )
}

export default Dashboard