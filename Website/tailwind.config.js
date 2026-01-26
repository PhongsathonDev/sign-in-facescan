/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    darkMode: "class", // ใช้ class เพื่อคุม Dark Mode เอง
    theme: {
        extend: {
            colors: {
                "primary": "#7f13ec",
                "primary-dark": "#6c10c9",
                "background-light": "#f7f6f8",
                "background-dark": "#191022",
            },
            fontFamily: {
                "display": ["Lexend", "sans-serif"],
                "body": ["Noto Sans", "sans-serif"]
            },
            // เพิ่ม Keyframes สำหรับอนิเมชั่นใน Config เลย เพื่อความชัวร์
            animation: {
                'gradient-xy': 'gradient-xy 15s ease infinite',
            },
            keyframes: {
                'gradient-xy': {
                    '0%, 100%': {
                        'background-size': '400% 400%',
                        'background-position': '0% 50%'
                    },
                    '50%': {
                        'background-size': '400% 400%',
                        'background-position': '100% 50%'
                    },
                }
            }
        },
    },
    plugins: [],
}