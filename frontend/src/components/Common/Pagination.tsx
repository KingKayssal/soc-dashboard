import React from "react";

interface PaginationProps {
  total: number;
  limit: number;
  offset: number;
  onPageChange: (newOffset: number) => void;
  onLimitChange: (newLimit: number) => void;
}

export function Pagination({
  total,
  limit,
  offset,
  onPageChange,
  onLimitChange,
}: PaginationProps) {
  const currentPage = Math.floor(offset / limit) + 1;
  const totalPages = Math.ceil(total / limit) || 1;
  const fromItem = total > 0 ? offset + 1 : 0;
  const toItem = Math.min(offset + limit, total);

  return (
    <div className="pagination-bar">
      <div>
        Showing <strong style={{ color: "var(--text-primary)" }}>{fromItem}</strong> -{" "}
        <strong style={{ color: "var(--text-primary)" }}>{toItem}</strong> of{" "}
        <strong style={{ color: "var(--text-primary)" }}>{total}</strong> alerts
      </div>

      <div className="pagination-controls">
        <div style={{ display: "flex", alignItems: "center", gap: "0.4rem", marginRight: "0.5rem" }}>
          <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>Rows per page:</span>
          <select
            className="filter-select"
            value={limit}
            onChange={(e) => onLimitChange(Number(e.target.value))}
            style={{ padding: "0.25rem 0.5rem" }}
          >
            <option value={25}>25</option>
            <option value={50}>50</option>
            <option value={100}>100</option>
          </select>
        </div>

        <button
          className="btn btn-secondary btn-sm"
          disabled={offset <= 0}
          onClick={() => onPageChange(Math.max(0, offset - limit))}
          title="Previous Page"
        >
          ← Prev
        </button>

        <span style={{ fontSize: "0.8rem", padding: "0 0.5rem" }}>
          Page <strong>{currentPage}</strong> of <strong>{totalPages}</strong>
        </span>

        <button
          className="btn btn-secondary btn-sm"
          disabled={offset + limit >= total}
          onClick={() => onPageChange(offset + limit)}
          title="Next Page"
        >
          Next →
        </button>
      </div>
    </div>
  );
}
