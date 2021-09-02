import { useTable } from 'react-table'
import styled from 'styled-components'

const TableDiv = styled.div`
    max-height: 94%;
    overflow: auto;
    border-width: 0.1em;
    border-style: solid;
`;

const Styledtable = styled.table`
    width: 100%;
    font-family: Arial, Helvetica, sans-serif;
    border-collapse: collapse;

    td, th {
        border: 1px solid #ddd;
        padding: 8px;
    }

    tr:nth-child(even){background-color: #f2f2f2;}

    tr:hover {background-color: #c0bfb0;}

    th, tfoot td{
        padding-top: 12px;
        padding-bottom: 12px;
        text-align: center;
        background-color: #4CAF50;
        color: white;
    }
`;

const Table = ({ columns, data }) => {

    const {
        getTableProps,
        getTableBodyProps,
        headerGroups,
        rows,
        prepareRow
    } = useTable({
        columns: columns,
        data: data
    })

    return (
        <TableDiv>
            <Styledtable {...getTableProps}>
                <thead>
                    {headerGroups.map((headerGroup) => (
                            <tr {...headerGroup.getHeaderGroupProps()}>
                                {headerGroup.headers.map( column => (
                                    <th {...column.getHeaderProps()}>{column.render('Header')}</th>
                                ))}
                            </tr>
                        ))}
                </thead>
                <tbody {...getTableBodyProps}>
                    {rows.map((row) => {
                        prepareRow(row)
                        return <tr {...row.getRowProps()}>
                            {row.cells.map( cell => (
                                <td {...cell.getCellProps}>{cell.render('Cell')}</td>
                            ))}
                        </tr>
                    })}
                </tbody>
            </Styledtable>
        </TableDiv>
    )
}

export default Table