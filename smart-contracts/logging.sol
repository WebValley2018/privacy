pragma solidity ^0.4.0;

contract Logging
{
    mapping (string=>string) events;

    function addEvent(string event_id, string json) public
    {
        events[event_id] = json;
    }
    
    function getEvent(string event_id) view public returns (string)
    {
        return events[event_id];
    }
}