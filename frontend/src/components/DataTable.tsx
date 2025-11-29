import { useState } from 'react'
import {
  useReactTable,
  getCoreRowModel,
  getPaginationRowModel,
  getSortedRowModel,
  getFilteredRowModel,
  flexRender,
  ColumnDef,
  SortingState,
  ColumnFiltersState,
} from '@tanstack/react-table'
import { ChevronUp, ChevronDown, ChevronsUpDown } from 'lucide-react'

interface DataTableProps {
  data: any[][]
  columns: string[]
  totalRows?: number
  currentPage: number
  pageSize: number
  onPageChange: (page: number) => void
}

export default function DataTable({
  data,
  columns,
  totalRows,
  currentPage,
  pageSize,
  onPageChange,
}: DataTableProps) {
  const [sorting, setSorting] = useState<SortingState>([])
  const [columnFilters, setColumnFilters] = useState<ColumnFiltersState>([])

  // Convert array data to objects for TanStack Table
  const tableData = data.map((row) => {
    const obj: Record<string, any> = {}
    columns.forEach((col, idx) => {
      obj[col] = row[idx]
    })
    return obj
  })

  // Create column definitions
  const columnDefs: ColumnDef<any>[] = columns.map((col) => ({
    accessorKey: col,
    header: ({ column }) => {
      return (
        <button
          onClick={() => column.toggleSorting(column.getIsSorted() === 'asc')}
          className="flex items-center space-x-1 hover:opacity-80 font-medium uppercase text-xs tracking-wider"
        >
          <span>{col}</span>
          {column.getIsSorted() === 'asc' ? (
            <ChevronUp className="h-3 w-3" />
          ) : column.getIsSorted() === 'desc' ? (
            <ChevronDown className="h-3 w-3" />
          ) : (
            <ChevronsUpDown className="h-3 w-3 opacity-40" />
          )}
        </button>
      )
    },
    cell: ({ getValue }) => {
      const value = getValue()
      if (value === null || value === undefined) {
        return <span style={{ color: '#8090a0', fontStyle: 'italic' }}>null</span>
      }
      const strValue = String(value)
      return (
        <div 
          style={{ 
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            whiteSpace: 'nowrap',
            maxWidth: '230px',
            width: '100%'
          }}
          title={strValue}
        >
          {strValue}
        </div>
      )
    },
  }))

  const table = useReactTable({
    data: tableData,
    columns: columnDefs,
    state: {
      sorting,
      columnFilters,
    },
    onSortingChange: setSorting,
    onColumnFiltersChange: setColumnFilters,
    getCoreRowModel: getCoreRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
  })

  return (
    <div className="space-y-4" style={{ width: '100%', maxWidth: '100%', overflow: 'hidden' }}>
      {/* Table Container with Horizontal and Vertical Scroll */}
      <div 
        className="overflow-x-scroll overflow-y-auto rounded-lg"
        style={{ 
          maxHeight: '500px',
          maxWidth: '100%',
          width: '100%',
          border: '1px solid rgba(168, 216, 255, 0.15)',
          backgroundColor: '#0d0d14',
          position: 'relative',
          overflowX: 'scroll',
          WebkitOverflowScrolling: 'touch'
        }}
      >
        <table style={{ width: 'auto', tableLayout: 'auto', minWidth: '100%' }}>
          <thead 
            className="sticky top-0 z-10"
            style={{ 
              backgroundColor: '#13131a', 
              borderBottom: '1px solid rgba(168, 216, 255, 0.15)'
            }}
          >
            {table.getHeaderGroups().map((headerGroup) => (
              <tr key={headerGroup.id}>
                {headerGroup.headers.map((header) => (
                  <th
                    key={header.id}
                    className="px-4 py-3 text-left whitespace-nowrap"
                    style={{ 
                      color: '#a8d8ff',
                      minWidth: '150px',
                      width: '200px',
                      maxWidth: '250px'
                    }}
                  >
                    {header.isPlaceholder
                      ? null
                      : flexRender(header.column.columnDef.header, header.getContext())}
                  </th>
                ))}
              </tr>
            ))}
          </thead>
          <tbody>
            {table.getRowModel().rows.map((row, idx) => (
              <tr
                key={row.id}
                className="hover:bg-opacity-80 transition-colors"
                style={{
                  backgroundColor: idx % 2 === 0 ? 'rgba(168, 216, 255, 0.02)' : 'transparent',
                  borderBottom: '1px solid rgba(168, 216, 255, 0.08)',
                }}
              >
                {row.getVisibleCells().map((cell) => (
                  <td
                    key={cell.id}
                    className="px-4 py-3 text-sm"
                    style={{ 
                      color: '#f0f0f5',
                      minWidth: '150px',
                      width: '200px',
                      maxWidth: '250px',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      whiteSpace: 'nowrap'
                    }}
                  >
                    {flexRender(cell.column.columnDef.cell, cell.getContext())}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination Controls */}
      <div className="flex items-center justify-between pt-2">
        <div className="text-sm" style={{ color: '#b0b8c0' }}>
          Page {currentPage} • Showing {data.length} rows
          {totalRows && ` of ~${totalRows.toLocaleString()} total`}
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => onPageChange(currentPage - 1)}
            disabled={currentPage === 1}
            className="px-4 py-2 rounded-lg transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
            style={{
              backgroundColor: 'rgba(168, 216, 255, 0.1)',
              color: '#a8d8ff',
              border: '1px solid rgba(168, 216, 255, 0.2)',
            }}
          >
            Previous
          </button>
          <button
            onClick={() => onPageChange(currentPage + 1)}
            disabled={!data.length || data.length < pageSize}
            className="px-4 py-2 rounded-lg transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
            style={{
              backgroundColor: 'rgba(168, 216, 255, 0.1)',
              color: '#a8d8ff',
              border: '1px solid rgba(168, 216, 255, 0.2)',
            }}
          >
            Next
          </button>
        </div>
      </div>
    </div>
  )
}

