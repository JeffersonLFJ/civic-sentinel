import React, { useState } from 'react';
import { AuditoriaSidebar } from './components/AuditoriaSidebar';
import { AuditoriaContent } from './components/AuditoriaContent';

export const AuditoriaPage = () => {
    const [selectedId, setSelectedId] = useState(null);

    return (
        <div className="flex h-full w-full">
            <AuditoriaSidebar onSelect={setSelectedId} selectedId={selectedId} />
            <AuditoriaContent selectedId={selectedId} />
        </div>
    );
};

export default AuditoriaPage;
