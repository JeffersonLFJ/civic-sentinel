import React from 'react';
import { Outlet } from 'react-router-dom';
import { Header } from './Header';

export const MainLayout = () => {
    return (
        <div className="flex flex-col h-screen bg-background text-text-main font-display overflow-hidden selection:bg-primary-soft selection:text-primary">
            <Header />
            <main className="flex-1 flex overflow-hidden relative">
                <Outlet />
            </main>
        </div>
    );
};
