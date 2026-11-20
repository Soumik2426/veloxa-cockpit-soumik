import type { LucideIcon } from 'lucide-react';

interface PagePlaceholderProps {
  title: string;
  description: string;
  icon: LucideIcon;
}

export default function PagePlaceholder({
  title,
  description,
  icon: Icon,
}: PagePlaceholderProps) {
  return (
    <div className="page-content">
      <div className="page-heading">
        <div>
          <div className="eyebrow">EXECUTIVE WORKSPACE</div>
          <h1>{title}</h1>
          <p>{description}</p>
        </div>
      </div>

      <section className="empty-state">
        <div className="empty-state-icon">
          <Icon size={27} strokeWidth={1.6} />
        </div>
        <h3>Workspace being configured</h3>
        <p>
          This section will be connected to the verified Veloxa backend
          functionality in the next implementation batch.
        </p>
      </section>
    </div>
  );
}