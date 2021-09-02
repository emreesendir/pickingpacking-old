import { useState } from 'react'
import styled from 'styled-components'
import Loading from '../../../../global/Loading'
import { post } from '../../../../global/Services'

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
    height: 30%;
    width: 30%;
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
    display: flex;
    justify-content: center;

    form{
        margin-top: 2em;
        width: 90%;
        height: 40%;
    }

    fieldset{
        height: 98%;
    }

`;

const InputDiv = styled.div`

    width: 70%;
    display: grid;
    grid-template-columns: auto auto;
    grid-row-gap: 0.3em;

`;

const CreateUser = ( { setStatus } ) => {

    let username;
    let password1;
    let password2;

    const changeUsername = (e) => {
        username = e.target.value;
    }

    const changePassword1 = (e) => {
        password1 = e.target.value;
    }

    const changePassword2 = (e) => {
        password2 = e.target.value;
    }

    const [loading, setLoading] = useState([false, '', ''])
    const submit = (e) => {
        e.preventDefault();

        setLoading([true, 'Sending data to server...', 'spinner']);

        post('management/users/', {'username': username, 'password1': password1, 'password2': password2}).then(res => {
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

    return (
        <>
            {loading[0] && <Loading message={loading[1]} symbol={loading[2]}/>}
            <Background/>
            <Div>
                <Cancel onClick={() => setStatus(false)}>X</Cancel>
                <DetailDiv>
                <form>
                    <fieldset>
                        <legend>Create User</legend>
                        <InputDiv>
                            <label htmlFor='username'>Username</label>
                            <input type='text' name='username' onChange={changeUsername}/>
                            <label htmlFor='username'>Password</label>
                            <input type='password' name='username' onChange={changePassword1}/>
                            <label htmlFor='username'>Confirm Password</label>
                            <input type='password' name='username' onChange={changePassword2}/>
                        </InputDiv>
                        <div style={{marginTop: '0.5em'}}>
                            <button onClick={submit}>Submit</button>
                        </div>
                    </fieldset>
                    </form>
                </DetailDiv>
            </Div>
        </>
    )
}

export default CreateUser