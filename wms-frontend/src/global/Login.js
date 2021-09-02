import { useState, useEffect, useRef } from 'react'
import { useHistory } from 'react-router-dom'
import styled from 'styled-components'
import { checkAccessRights, login } from './Services'
import Loading from './Loading'

const Div = styled.div`
    height: 100%;
    display: flex;
    justify-content: top;
    align-items: center;
    flex-direction: column;

    div{
        margin-top: 10%;
    }

    form {
        width: 20em;
        border-style: solid;
        border-width: 0.1em;
        padding: 2em 1em 3em 1em;
    }

    .input {
        display: flex;
        margin: 0.5em 2em 0.5em 2em;

        input {
            margin-left: auto;
            width: 12em;
        }
    }

    #loginButon {
        margin-top: 1em;
        width: 6em;
        height: 3em;
    }
`;

const Login = () => {
    const history = useRef();
    history.current = useHistory();

    useEffect(() => checkAccessRights().then(access => access && history.current.push('/menu')), [])

    const [loading, setLoading] = useState([false, '', ''])

    let username;
    let password;

    const Login = (e) => {
        e.preventDefault();
        setLoading([true, 'Logging in...', 'spinner']);

        login(e, username, password)
            .then(isSucceed => {
                if(isSucceed) {
                    setLoading([true, 'Login successful.', 'done']);
                    setTimeout(() => {
                        setLoading([false, '', '']);
                    }, 2000);
                    history.current.push('/menu');
                }else{
                    setLoading([true, 'Failed to login!', 'error']);
                    setTimeout(() => {
                        setLoading([false, '', '']);
                    }, 2000);
                }
            })
            .catch(err => {
                console.error(err);
                setLoading([true, 'Failed to login!', 'error']);
                setTimeout(() => {
                    setLoading([false, '', '']);
                }, 2000);
            });

        //clean the form
        const pass = document.getElementById('password');
        const usr = document.getElementById('username');
        pass.value = '';
        usr.value = '';
        username = '';
        password = '';
    }

    return (
        <>
            {loading[0] && <Loading message={loading[1]} symbol={loading[2]}/>}
            <Div>
                <div>
                    <form style={{textAlign: 'center', margin: 5}}>
                        <legend></legend>
                        <p>Warehouse Management System</p>
                        <hr/>
                        <div className='input'>
                            <label>Username</label>
                            <input id='username' type='text' onChange={e => username = e.target.value}/>
                        </div>
                        <div className='input'>
                            <label>Password</label>
                            <input id='password' type='password' onChange={e => password = e.target.value}/>
                        </div>
                        <input id='loginButon' type='submit' value='Login' onClick={Login}/>
                    </form>
                </div>
            </Div>
        </>
    )
}

export default Login