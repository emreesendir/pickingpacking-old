import styled from 'styled-components'
import ClipLoader from "react-spinners/RingLoader";
import { VscError } from 'react-icons/vsc'
import { IoCheckmarkDoneSharp } from 'react-icons/io5'

const Div = styled.div`
    position: absolute;
    top: 0;
    background-color: black;
    opacity: 0.2;
    height: 100%;
    width: 100%;
    z-index: 10;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
`;

const P = styled.p`
    margin-top: 2em;
    font-size: 150%;
    color: #ebdc09;
`;

const Icon = styled.i`
    font-size: 600%;
    color: #ebdc09;
`;

const Loading = ({ message, symbol }) => {
    return (
        <Div>
            {symbol === 'spinner' && <ClipLoader color={'#ebdc09'} loading={true} css={''} size={150} />}
            {symbol === 'error' && <Icon><VscError /></Icon>}
            {symbol === 'done' && <Icon><IoCheckmarkDoneSharp /></Icon>}
            <P>{message}</P>
        </Div>
    )
}

export default Loading