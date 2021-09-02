import styled from 'styled-components'
import Sizing from './Sizing'
import OnHold from './OnHold'
import Inprogress from './Inprogress'
import Archive from './Archive'
import Users from './Users'

const Div = styled.div`
    border-style: solid;
    height: 97%;
    overflow: auto;
`;

const Content = ({ activePage, accessrights }) => {
    return (
        <Div>
            {(activePage === 'Sizing' && accessrights.includes('Manage | Sizing')) && <Sizing />}
            {(activePage === 'On Hold' && accessrights.includes('Manage | On Hold')) && <OnHold />}
            {(activePage === 'In Progress' && accessrights.includes('Manage | In Progress')) && <Inprogress />}
            {(activePage === 'Archive' && accessrights.includes('Manage | Archive')) && <Archive />}
            {(activePage === 'Users' && accessrights.includes('Manage | Users')) && <Users />}
        </Div>
    )
}

export default Content