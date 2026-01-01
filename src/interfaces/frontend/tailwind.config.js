/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            colors: {
                primary: "#4F7767", // Earthy green/teal
                "primary-hover": "#3C5E51",
                "primary-soft": "#E8F3EE", // Very light green
                background: "#F5F5F0", // Warm off-white/beige
                surface: "#FFFFFF",
                "text-main": "#2C3E36", // Dark green/grey
                "text-secondary": "#5D6B65", // Muted green/grey
                "text-muted": "#94A39D",
                border: "#E0E5E2",
                "background-light": "#F9FAF9",
                "accent-blue": "#6096BA", // Soft blue for accents
                "accent-orange": "#E69F73" // Soft terracotta
            },
            fontFamily: {
                display: ["Public Sans", "sans-serif"],
                body: ["Noto Sans", "sans-serif"]
            },
            borderRadius: {
                lg: "0.5rem",
                xl: "0.75rem",
                "2xl": "1rem",
                "3xl": "1.5rem",
            },
            boxShadow: {
                soft: "0 4px 20px -2px rgba(44, 62, 54, 0.04)",
                card: "0 2px 8px 0 rgba(44, 62, 54, 0.04), 0 1px 2px 0 rgba(44, 62, 54, 0.02)"
            }
        },
    },
    plugins: [],
}
