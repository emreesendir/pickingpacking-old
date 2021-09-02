import styled from 'styled-components'
import { useState, useEffect } from 'react'
import { get, patch, dlete } from '../../../../global/Services'
import { MdDelete, MdEdit, MdSave, MdCancel  } from 'react-icons/md'
import Loading from '../../../../global/Loading'

const Background = styled.div`

    position: absolute;
    top: 0;
    background-color: black;
    opacity: 0.2;
    height: 100%;
    width: 100%;
    z-index: 2;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;

`;

const Div = styled.div`

    position: absolute;
    z-index: 3;
    height: 50%;
    width: 50%;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;

`;

const Cancel = styled.button`

    margin-left: auto;
    margin-bottom: 0.5em;
    cursor: pointer;

`;

const DetailDiv = styled.div`

    border-style: solid;
    height: 100%;
    width: 100%;
    background-color: #f0f0f0;
    color: black;
    text-align: left;

    form{
        margin-left: 2em;
        width: 90%;
        height: 40%;
    }

    fieldset{
        height: 98%;
    }

`;

const Permissions = styled.div`

    height: 90%;
    overflow-x: auto;
    display: grid;
    grid-template-rows: 1fr 1fr 1fr 1fr 1fr 1fr 1fr 1fr;
    grid-auto-flow: column;

`;

const Header = styled.div`

    margin-left: 2em;
    width: 90%;
    display: flex;
    align-items: center;

    div{
        margin-left: auto;
        margin-right: 0.5em;
        font-size: 110%;
    }

`;

const ConfirmBackground = styled.div`
    
    position: absolute;
    z-index: 5;
    height: 100%;
    width: 100%;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    background-color: black;
    opacity: 0.2;
    top: 0;
`;

const Confirm = styled.div`
    
    position: absolute;
    z-index: 6;
    height: 20%;
    width: 20%;
    background-color: #f0f0f0;
    border-style: solid;
`;

const UserDetail = ( { userId, setStatus } ) => {

    const [loading, setLoading] = useState([false, '', ''])
    const [DATA, setDATA] = useState(false)
    const [editMode, setEditMode] = useState(false)
    const [confirm, setConfirm] = useState(false)

    const getData = () => {
        get(`management/users/${userId}/`).then(data => {
            data.allpermissions.sort();
            setDATA(data)
        })
    }

    useEffect(getData, [userId, editMode])

    const permissonChange = (e) => {
        let data = DATA;
        if(data.userpermissions.includes(e.target.value)){
            data.userpermissions.splice(data.userpermissions.indexOf(e.target.value), 1);
        }else{
            data.userpermissions.push(e.target.value)
        }
        setDATA({...data});
    }

    const clickSave = () => {
        setLoading([true, 'Sending data to server...', 'spinner']);

        patch('management/users/', {'id': userId, 'permissions': DATA.userpermissions}).then(res => {
            if(res){
                setLoading([true, 'Successfull.', 'done']);
                setTimeout(() => {
                    setLoading([false, '', '']);
                    setEditMode(false);
                }, 1000)
            }else{
                setLoading([true, '! SERVER ERROR !', 'error']);
                setTimeout(() => {
                    setLoading([false, '', '']);
                    setEditMode(false);
                }, 1000)
            }
        })
    }

    const clickCancel = () => {
        setEditMode(false);
    }

    const clickEdit = () => {
        setEditMode(true)
    }

    const dlt = () => {
        setLoading([true, 'Sending data to server...', 'spinner']);

        dlete(`management/users/${userId}/`).then(res => {
            if(res){
                setLoading([true, 'Successfull.', 'done']);
                setTimeout(() => {
                    setLoading([false, '', '']);
                    setStatus(false);
                }, 1000)
            }else{
                setLoading([true, '! SERVER ERROR !', 'error']);
                setTimeout(() => {
                    setLoading([false, '', '']);
                    setStatus(false);
                }, 1000)
            }
        })
    }

    const clickDelete = () => {
        setConfirm(true)
    }

    return (
        <>
            {confirm && 
                <>
                    <ConfirmBackground/>
                    <Confirm>
                        <div>
                            <p>Are you sure?</p>
                            <button onClick={() => {setConfirm(false); dlt();}}>Delete</button>
                            <button onClick={() => {setConfirm(false);}}>Cancel</button>
                        </div>
                    </Confirm>
                </>}
            {loading[0] && <Loading message={loading[1]} symbol={loading[2]}/>}
            <Background/>
            <Div>
                <Cancel onClick={() => setStatus(false)}>X</Cancel>
                {DATA && <DetailDiv>
                    <Header>
                        <h1>{DATA.username}</h1>
                        <div>
                            {editMode && <>
                                <MdSave style={{margin: '0.5em', cursor: 'pointer'}} onClick={clickSave}/>
                                <MdCancel style={{margin: '0.5em', marginRight: '0', cursor: 'pointer'}} onClick={clickCancel}/>
                            </>}
                            {!editMode && <>
                                <MdEdit style={{margin: '0.5em', cursor: 'pointer'}} onClick={clickEdit}/>
                                <MdDelete style={{margin: '0.5em', marginRight: '0', cursor: 'pointer'}} onClick={clickDelete}/>
                            </>}
                        </div>
                    </Header>
                    <form>
                        <fieldset disabled={!editMode}>
                            <legend>Permissions</legend>
                            <Permissions>
                                {DATA.allpermissions.map(permission => {
                                    if(DATA.userpermissions.includes(permission)){
                                        return(
                                            <div>
                                                <input onChange={permissonChange} type="checkbox" id={permission} name={permission} value={permission} checked/>
                                                <label htmlFor={permission}>{permission}</label>
                                            </div>
                                        )
                                    }else{
                                        return(
                                            <div>
                                                <input onChange={permissonChange} type="checkbox" id={permission} name={permission} value={permission}/>
                                                <label htmlFor={permission}>{permission}</label>
                                            </div>
                                        )
                                    }
                                })}
                            </Permissions>
                        </fieldset>
                    </form>
                </DetailDiv>}
            </Div>
        </>
    )
}

export default UserDetail