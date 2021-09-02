import { useEffect, useRef, useState } from 'react'
import { Link, useHistory } from 'react-router-dom'
import styled from 'styled-components'
import User from './User'
import { checkAccessRights } from './Services'

const Div = styled.div`
    height: 100%;
    display: flex;
    flex-direction: column;
    justify-content: top;
    align-items: center;

    h1{
        margin-top: 10%;
    }

    div{
        border-style: solid;
        display: grid;
        grid-template-columns: 12em 12em 12em;
        justify-items: center;
        align-items: center;
    }

    button{
        margin: 5em;
        height: 5em;
        width: 8em;

            @media screen and (max-width: 800px){
            font-size: 90%;
            margin: 2em;
        }
    }

    @media screen and (max-width: 800px){
        font-size: 60%;
    }
`;

const UserDiv = styled.div`
    position: absolute;
    right: 1em;
    top: 1em;

    @media screen and (max-width: 800px){
        font-size: 60%;
    }
`;

const Main = () => {
    const [accessrights, setAccessrights] = useState([]);
    const history = useRef();
    history.current = useHistory();

    useEffect(() => checkAccessRights().then(access => access ? setAccessrights(access) : history.current.push('/login')), [])

    return (
        <>
            <UserDiv><User /></UserDiv>
            <Div>
                <h1>Main Menu</h1>
                <div>
                    {accessrights.includes('Modules | Manage') && <Link to='/manage'><button>Manage</button></Link>}
                    {accessrights.includes('Modules | Picking') && <Link to='/picking'><button>Picking</button></Link>}
                    {accessrights.includes('Modules | Packing') && <Link to='/packing'><button>Packing</button></Link>}
                    {accessrights.includes('Modules | Dashboard') && <Link to='/dashboard'><button>Dashboard</button></Link>}
                </div>
            </Div>
        </>
    )
}

export default Main