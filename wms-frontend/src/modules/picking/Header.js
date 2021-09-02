import styled from 'styled-components'
import { Link } from 'react-router-dom'
import { IoMdArrowBack } from 'react-icons/io'
import User from '../../global/User'

const StyledHeader = styled.header`
    display: flex;
    align-items: center;
    margin-top: 0.5em;

    @media screen and (max-width: 800px){
        font-size: 60%;
    }
`;

const Menuicon = styled.i`
    font-size: 3em;
    width: 1em;
    height: 1em;
    margin: 0.3em;
    margin-left: 0.5em;
    padding: 0;
    background-color: #b3b3b3;

    a:visited{
        color: #575757;
    }

    @media screen and (max-width: 700px){
        font-size: 2em;
    }
`;

const Title = styled.h2`

`;

const Styleduser = styled.div`
    margin-left: auto;
    margin-right: 1em;
`;

const Header = () => {
    return(
        <StyledHeader>
            <Menuicon><Link to='/menu' style={{display: 'flex', alignItems: 'center'}}><IoMdArrowBack /></Link></Menuicon>
            <Title>WMS Picking</Title>
            <Styleduser><User /></Styleduser>
        </StyledHeader>
    )
}

export default Header