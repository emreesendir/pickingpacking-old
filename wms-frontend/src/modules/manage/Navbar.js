import { useState } from 'react'
import styled from 'styled-components'

const Nav = styled.nav`
    display: flex;
    border-style: solid;
    height: 3em;
    overflow: auto;

    ul{
        list-style-type: none;
        display: flex;
        justify-content: space-between;
        padding-left: 0;
        margin: 0;
        align-items: center;
    }

    li{
        display: flex;
        justify-content: center;
        align-items: center;
        cursor: pointer;
        width: 5em;
        height: auto;
        padding: 0.3em;
        margin: 0.7em;
    }

    @media screen and (max-width: 700px){
        font-size: 60%;
    }
`;

const Navbar = ({ setActivePage, accessrights }) => {

    const [selected, setSelected] = useState('On Hold')

    const refreshPage = (e) => {
        if (e.target.localName === 'li') {
            setSelected(e.target.innerText);
            setActivePage(e.target.innerText)
        }
    }

    return (
        <Nav>
            <ul onClick={refreshPage}>
                {accessrights.includes('Manage | On Hold') && <li style={selected === 'On Hold' ? {color: 'red', backgroundColor: 'lightblue'} : {color: 'red'}}>On Hold</li>}
                {accessrights.includes('Manage | Sizing') && <li style={selected === 'Sizing' ? {backgroundColor: 'lightblue'} : {}}>Sizing</li>}
                {accessrights.includes('Manage | In Progress') && <li style={selected === 'In Progress' ? {backgroundColor: 'lightblue'} : {}}>In Progress</li>}
                {accessrights.includes('Manage | Archive') && <li style={selected === 'Archive' ? {backgroundColor: 'lightblue'} : {}}>Archive</li>}
                {accessrights.includes('Manage | Users') && <li style={selected === 'Users' ? {backgroundColor: 'lightblue'} : {}}>Users</li>}
            </ul>
        </Nav>
    )
}

export default Navbar