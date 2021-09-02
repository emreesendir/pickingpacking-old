import styled from 'styled-components'
import { useState, useEffect } from 'react'
import Table from '../../../global/Table'
import { get } from '../../../global/Services'
import Detail from './components/Detail'

//#region style
const Outerdiv = styled.div`
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    height: 95%;
`;

const Div = styled.div`
    width: 90%;
    height: 95%;
    overflow: auto;
    margin-top: 20px;
    display: flex;
    flex-direction: column;
    justify-content: top;
    border-style: solid;

    @media screen and (max-width: 700px){
        font-size: 70%;
    }
`;

const BottomDiv = styled.div`
    width: 100%;
    height: 6%;
    display: flex;
    margin-top: auto;
    border-top: solid 0.1em;
`;

//#endregion

//#region column setup

const COLUMNS = [
    {
        Header: 'Remote Id',
        Footer: 'Remote Id',
        accessor: 'remoteId'
    },
    {
        Header: 'Order',
        Footer: 'Order',
        accessor: data => {
            return (
                <>
                    {data.productLines.map(line => 
                        <p style={{textAlign: 'left', marginLeft: '1em'}}>• {line.quantity} piece(s) {line.name}. Location: {line.location}</p>
                    )}
                </>
            )
        }
    },
    {
        Header: 'Status',
        Footer: 'Status',
        accessor: 'status'
    },
    {
        Header: 'Commands',
        Footer: 'Commands',
        accessor: data => {
            return (
                <>
                    {data.commands.split('.').map(command => 
                        <p>{command}</p>)}
                </>
            )
        }
    },
    {
        Header: 'Detail',
        Footer: 'Detail',
        accessor: data => <button id={data.id}>{'Detail >>'}</button>
    }
]

//#endregion

let orderId;

const Inprogress = () => {
    // Table
    const [DATA, setDATA] = useState([])

    const refreshTable = () => {
        get('management/inprogress/').then(data => {
            setDATA([]);
            setDATA(data)
        })
    }

    useEffect(refreshTable, [])

    //Detail
    const [detailStatus, setDetailStatus] = useState(false);

    const click = e => {
        if (e.target.tagName === 'BUTTON') {
            orderId = e.target.id;
            setDetailStatus(true);
        }
    }

    return (
        <Outerdiv>
            {detailStatus && <Detail orderId={orderId} setStatus={setDetailStatus}/>}
            <Div onClick={click}>
                <Table data={DATA} columns={COLUMNS}/>
                <BottomDiv>
                </BottomDiv>
            </Div>
        </Outerdiv>
    )
}

export default Inprogress