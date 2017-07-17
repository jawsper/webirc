import React from 'react';
import ReactDOM from 'react-dom';


var test_events = [
    {id: 1, type: 'privmsg', source: 'bob!bob@bob.nl', time: '2017-07-15 00:45:15', text: 'hoi'},
    {id: 2, type: 'notice', source: 'bob!bob@bob.nl', time: '2017-07-15 00:45:15', text: 'hoi'},
    {id: 3, type: 'action', source: 'bob!bob@bob.nl', time: '2017-07-15 00:45:15', text: 'hoi'},
    {id: 4, type: 'join', source: 'bob!bob@bob.nl', time: '2017-07-15 00:45:15'},
    {id: 5, type: 'part', source: 'bob!bob@bob.nl', time: '2017-07-15 00:45:15', reason: 'Screw you guys'},
    {id: 6, type: 'quit', source: 'bob!bob@bob.nl', time: '2017-07-15 00:45:15', reason: 'Ping timeout'},
    {id: 7, type: 'kick', source: 'jawsper!jawsper@jawsper.nl', target: 'bob!bob@bob.nl', time: '2017-07-15 00:45:15', reason: 'Silly bob'},
]

class NameDisplay extends React.Component
{
    display_name(name)
    {
        if(!name) return name;
        let split_pos = name.indexOf('!');
        if(split_pos > 0) name = name.substring(0, split_pos);
        return name;
    }
    render()
    {
        return <span className="name" title={this.props.name}>{this.display_name(this.props.name)}</span>;
    }
}

class TimeDisplay extends React.Component
{
    render()
    {
        return <span className="time" title={this.props.time}>{this.props.time}</span>;
    }
}

class EventBase extends React.Component
{
    render()
    {
        return <div className={'event event-' + this.props.cls} id={'event-' + this.props.id}>{this.props.children}</div>
    }
}

class EventPrivmsg extends React.Component
{
    render()
    {
        return (
            <EventBase id={this.props.id} cls="message">
                <NameDisplay name={this.props.source} />
                {' '}
                <TimeDisplay time={this.props.time} />
                <br />
                <span className="text">{this.props.text}</span>
            </EventBase>
        );
    }
}

class EventNotice extends React.Component
{
    render()
    {
        return (
            <EventBase id={this.props.id} cls="message">
                <NameDisplay name={this.props.source} />
                {' '}
                <TimeDisplay time={this.props.time} />
                <br />
                <i>[notice] </i><span className="text">{this.props.text}</span>
            </EventBase>
        );
    }
}

class EventAction extends React.Component
{
    render()
    {
        return (
            <EventBase id={this.props.id} cls="message">
                <NameDisplay name={this.props.source} />
                {' '}
                <TimeDisplay time={this.props.time} />
                <br />
                <i>[action] </i><span className="text">{this.props.text}</span>
            </EventBase>
        );
    }
}

class EventJoin extends React.Component
{
    render()
    {
        return (
            <EventBase id={this.props.id} cls="info">
                <NameDisplay name={this.props.source} />
                {' joined the channel '}
                <TimeDisplay time={this.props.time} />
            </EventBase>
        )
    }
}

class EventPart extends React.Component
{
    render()
    {
        return (
            <EventBase id={this.props.id} cls="info">
                <NameDisplay name={this.props.source} />
                {' left the channel (' + this.props.reason + ') '}
                <TimeDisplay time={this.props.time} />
            </EventBase>
        )
    }
}

class EventQuit extends React.Component
{
    render()
    {
        return (
            <EventBase id={this.props.id} cls="info">
                <NameDisplay name={this.props.source} />
                {' quit (' + this.props.reason + ') '}
                <TimeDisplay time={this.props.time} />
            </EventBase>
        )
    }
}

class EventKick extends React.Component
{
    render()
    {
        return (
            <EventBase id={this.props.id} cls="info">
                <NameDisplay name={this.props.source} />
                {' kicked '}
                <NameDisplay name={this.props.target} />
                {' from the channel (' + this.props.reason + ') '}
                <TimeDisplay time={this.props.time} />
            </EventBase>
        )
    }
}

class Event extends React.Component
{
    render()
    {
        var inner_event = {
            privmsg: EventPrivmsg,
            notice: EventNotice,
            action: EventAction,
            join: EventJoin,
            part: EventPart,
            quit: EventQuit,
            kick: EventKick,
        }[this.props.type];
        if(!inner_event) return null;
        return React.createElement(inner_event, this.props);
    }
}

class EventContainer extends React.Component
{
    render()
    {
        var children = this.props.events.map(function(event)
        {
            event.key = event.id;
            return React.createElement(Event, event);
        });

        return (
            <div className="col-sm-12 col-md-12 output">
                {children}
            </div>
        );
    }
}

const eventContainer = <EventContainer />;
// eventContainer.setState({
//     'events': test_events
// })

class TabButton extends React.Component
{
    constructor(props)
    {
        super(props);
        this.onClick = this.onClick.bind(this);
    }

    onClick(e)
    {
        this.props.onClick();
        e.preventDefault();
        return false;
    }

    render()
    {
        var className = 'tab-nav';
        if(this.props.active) className += ' active';
        return (
    <li id={'tab_' + this.props.id} className={className} data-id={this.props.id}>
        <a onClick={this.onClick} href={'#panel_' + this.props.id}>
            <span className="title">{this.props.title}</span>
            {' '}
            <span className="close-tab glyphicon glyphicon-remove" title="Close tab"></span>
        </a>
    </li>
        );
    }
}

class TabFrame extends React.Component
{
    render()
    {
        var className = 'tab-pane';
        if(this.props.active) className += ' active';
        return (
    <div className={className} data-id={this.props.id} id={'panel_' + this.props.id}>
        <div className="row">
            <div className="col-sm-10 col-md-10">
                <div className="topic-parent"><span className="topic">!topic!</span></div>
            </div>
            <div className="col-sm-2 col-md-2 names-header">!names header!</div>
            <div className="col-sm-10 col-md-10 output-parent">
                <EventContainer events={this.props.events} />
                <div className="col-sm-12 col-md-12 output">!messages {this.props.title} !</div>
            </div>
            <div className="col-sm-2 col-md-2 names-parent">
                <div className="names">!names here!</div>
            </div>
        </div>
    </div>
        );
    }
}

class TabContainer extends React.Component
{
    constructor(props)
    {
        super(props);
        this.state = {
            activeFrame: 1
        }
    }

    render()
    {
        var tab_buttons = [];
        var tab_frames = [];

        this.props.tab_list.forEach((tab) => {
            tab_buttons.push(<TabButton 
                onClick={() => this.setState({activeFrame: tab.id})} 
                key={tab.id} 
                id={tab.id} 
                title={tab.title} 
                active={this.state.activeFrame == tab.id} />);
            tab_frames.push(<TabFrame 
                key={tab.id} 
                id={tab.id} 
                title={tab.title} 
                active={this.state.activeFrame == tab.id}
                events={tab.events} />);
        });

        return (
            <div className="tab_container">
                <ul className="nav nav-tabs" role="tablist">{tab_buttons}</ul>
                <div className="tab-content">{tab_frames}</div>
            </div>
        )
    }
}

class InputField extends React.Component
{
    constructor(props)
    {
        super(props);
    }

    render()
    {
        return (
            <div className="form-group">
                <input id="input" className="form-control input" placeholder="Message" autoComplete="off" />
            </div>
        );
    }
}

class WebIRCRoot extends React.Component
{
    constructor(props)
    {
        super(props);
        this.state = {
            tab_list: [
                {id: 1, title: 'bob', events: []},
                {id: 2, title: '#fiets', events: []}
            ]
        }
    }
    render()
    {
        return (
            <div>
                <TabContainer tab_list={this.state.tab_list} />
                <br />
                <InputField />
            </div>
        );
    }
}

ReactDOM.render(<WebIRCRoot />, document.getElementById('root'));