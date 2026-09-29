import { ChevronLeft, ChevronRight } from "lucide-react"
import { Button } from "./button"
import { cn } from "@/utils"

export interface PaginationProps {
  currentPage: number
  totalPages: number
  totalCount?: number
  pageSize?: number
  onPageChange: (page: number) => void
  className?: string
}

export function Pagination({
  currentPage,
  totalPages,
  totalCount,
  pageSize = 10,
  onPageChange,
  className,
}: PaginationProps) {
  if (totalPages <= 1 && (totalCount === undefined || totalCount === 0)) {
    return null
  }

  const startItem = totalCount ? (currentPage - 1) * pageSize + 1 : undefined
  const endItem = totalCount
    ? Math.min(currentPage * pageSize, totalCount)
    : undefined

  const getPageNumbers = () => {
    const pages: number[] = []
    const maxVisible = 5
    let start = Math.max(1, currentPage - Math.floor(maxVisible / 2))
    const end = Math.min(totalPages, start + maxVisible - 1)

    if (end - start + 1 < maxVisible) {
      start = Math.max(1, end - maxVisible + 1)
    }

    for (let i = start; i <= end; i++) {
      pages.push(i)
    }
    return pages
  }

  const pageNumbers = getPageNumbers()

  return (
    <div
      className={cn(
        "flex flex-col sm:flex-row items-center justify-between gap-4 py-4",
        className,
      )}
    >
      <div className="text-sm text-muted-foreground">
        {totalCount !== undefined &&
        startItem !== undefined &&
        endItem !== undefined ? (
          <span>
            Showing{" "}
            <strong className="font-medium text-foreground">{startItem}</strong>{" "}
            to{" "}
            <strong className="font-medium text-foreground">{endItem}</strong>{" "}
            of{" "}
            <strong className="font-medium text-foreground">
              {totalCount}
            </strong>{" "}
            results
          </span>
        ) : (
          <span>
            Page{" "}
            <strong className="font-medium text-foreground">
              {currentPage}
            </strong>{" "}
            of{" "}
            <strong className="font-medium text-foreground">
              {totalPages}
            </strong>
          </span>
        )}
      </div>

      <div className="flex items-center space-x-1">
        <Button
          variant="outline"
          size="sm"
          onClick={() => onPageChange(currentPage - 1)}
          disabled={currentPage <= 1}
          aria-label="Previous page"
        >
          <ChevronLeft className="h-4 w-4 mr-1" />
          Previous
        </Button>

        {pageNumbers.map((page) => (
          <Button
            key={page}
            variant={page === currentPage ? "default" : "outline"}
            size="sm"
            className="w-9 h-8 p-0"
            onClick={() => onPageChange(page)}
            aria-label={`Go to page ${page}`}
            aria-current={page === currentPage ? "page" : undefined}
          >
            {page}
          </Button>
        ))}

        <Button
          variant="outline"
          size="sm"
          onClick={() => onPageChange(currentPage + 1)}
          disabled={currentPage >= totalPages}
          aria-label="Next page"
        >
          Next
          <ChevronRight className="h-4 w-4 ml-1" />
        </Button>
      </div>
    </div>
  )
}
