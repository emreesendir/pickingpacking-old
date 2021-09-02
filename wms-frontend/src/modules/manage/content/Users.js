import styled from 'styled-components'
import { useState, useEffect } from 'react'
import Table from '../../../global/Table'
import { get } from '../../../global/Services'
import UserDetail from './components/UserDetail'
import CreateUser from './components/CreateUser'

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

    button{
        margin: 0.5em 0.5em 0.5em auto;
    }
`;

//#endregion

//#region column setup

const COLUMNS = [
    {
        Header: 'ID',
        Footer: 'ID',
        accessor: 'id'
    },
    {
        Header: 'Username',
        Footer: 'Username',
        accessor: 'username'
    },
    {
        Header: 'Detail',
        Footer: 'Detail',
        accessor: data => <button id={data.id}>{'Detail >>'}</button>
    }
]

//#endregion

let userId;

const Users = () => {
    // Table
    const [DATA, setDATA] = useState([])

    const refreshTable = () => {
        get('management/users/').then(data => {
            setDATA([]);
            setDATA(data)
        })
    }

    useEffect(refreshTable, [])

    //Detail
    const [detailStatus, setDetailStatus] = useState(false);

    const clickDetail = e => {
        if (e.target.tagName === 'BUTTON') {
            userId = e.target.id;
            setDetailStatus(true);
        }
    }

    //Create User
    const [createUser, setCreateUser] = useState(false);

    const clickCreateUser = () => {
        setCreateUser(true)
    }

    
    useEffect(refreshTable, [detailStatus, createUser])

    return (
        <Outerdiv>
            {detailStatus && <UserDetail userId={userId} setStatus={setDetailStatus}/>}
            {createUser && <CreateUser setStatus={setCreateUser}/>}
            <Div>
                <div style={{height: '100%'}} onClick={clickDetail}><Table data={DATA} columns={COLUMNS}/></div>
                <BottomDiv>
                    <button onClick={clickCreateUser}>Create User</button>
                </BottomDiv>
            </Div>
        </Outerdiv>
    )
}

export default Users