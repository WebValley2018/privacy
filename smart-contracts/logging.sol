pragma solidity ^0.4.0;

contract Logging
{
    mapping (string=>string) events;
    string[] evids;

    function addEvent(string event_id, string json) public
    {
        events[event_id] = json;
        evids.push(event_id);
    }
    
    function getEvent(string event_id) view public returns (string)
    {
        return events[event_id];
    }

    function getEventsLength() view public returns (uint256){
        return evids.length;
    }
}