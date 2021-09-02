import { useHistory } from 'react-router-dom'
import styled from 'styled-components'

const Div = styled.div`
    display: flex;
    align-items: center;
    height: 2em;
    width: fit-content;
    border-style: solid;
    border-width: 0.1em;

    #username {
        margin-left: auto;
        margin-right: 0.5em;
        width: 8em;
        text-align: right;
    }

    #logout {
        margin-left: 0.5em;
        cursor: pointer;
        color: #ad73c9;
    }
`;

const User = () => {
    let history = useHistory();
    const username = localStorage.getItem('username');

    const logout = () => {
        localStorage.removeItem('username')
        localStorage.removeItem('token')
        history.push('/login')
    }

    return (
        <Div>
            <p id='logout' onClick={logout}>Logout</p>
            <p id='username'>{username}</p>
        </Div>
    )
}

export default User