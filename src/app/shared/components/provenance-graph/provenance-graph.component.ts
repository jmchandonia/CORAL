import { Component, OnInit, ElementRef, ViewChild, AfterViewInit, EventEmitter, Output } from '@angular/core';
import { Network, DataSet } from 'vis';
const mockData = require('src/app/shared/test/mock-provenance-graph.json');
import { QueryMatch } from 'src/app/shared/models/QueryBuilder';

@Component({
  selector: 'app-provenance-graph',
  templateUrl: './provenance-graph.component.html',
  styleUrls: ['./provenance-graph.component.css']
})
export class ProvenanceGraphComponent implements OnInit, AfterViewInit {

  nodes:  DataSet;
  edges: { from: number, to: number }[];
  @Output() querySelected: EventEmitter<QueryMatch> = new EventEmitter();

  @ViewChild('pGraph') pGraph: ElementRef;

  options = {
    interaction: {
      zoomView: false,
      dragView: false,
      hover: true
    },
    physics: {
      // enabled: false,
      hierarchicalRepulsion: {
        // avoidOverlap: 1
        // nodeDistance: 200
      }
    },
    layout: {
      hierarchical: {
        direction: 'UD',
        sortMethod: 'hubsize',
        nodeSpacing: 200,
        levelSeparation: 75,
      }
    },
    edges: {
      arrows: {
        to: {
          enabled: true,
        }
      },
    }
  };

  network: any; // TODO: see if there is @types/vis-network

  constructor(
  ) { }

  ngOnInit(): void {
  }

  ngAfterViewInit(): void {
    this.nodes = new DataSet(
      mockData.result.nodes.map(this.createNode)
    );

    this.edges = new DataSet(
      mockData.result.links.map(this.createEdge)
    );

    this.network = new Network(
      this.pGraph.nativeElement,
      {
        nodes: this.nodes,
        edges: this.edges
      },
      this.options
    );
    
    // set zoom level to contain all nodes
    this.network.fit({
      nodes: this.nodes.map(node => node.id),
      animation: true
    });

    // add double click event listener to submit search query on nodes
    this.network.on('doubleClick', (({nodes}) => {
      const { category, dataType, dataModel } = this.nodes.get(nodes)[0].data;
      const query = new QueryMatch({category, dataType, dataModel});
      this.querySelected.emit(query);
    }));
 }

 createNode(dataItem: any) {
  const node: any = {
    id: dataItem.index,
    label: dataItem.category !== 'null' ? `${dataItem.count} ${dataItem.name}` : '',
    font: {
      size: 16
    },
    color: {
      background: dataItem.category !== 'null' ? 'white' : 'rgba(0,0,0,0)',
      border: dataItem.category === 'DDT_' ? 'rgb(246, 139, 98)' : 'rgb(78, 111, 182)',
      hover: { background: '#ddd' }
    },
    borderWidth: dataItem.category === 'null' ? 0 : 1,
    physics: false,
    shape: 'box',
    data: {...dataItem}
  }
  return node;
 }

 createEdge(edgeItem: any) {
   return {
     from: edgeItem.source,
     to: edgeItem.target,
     label: 'label',
     font: {
       size: 16,
       color: 'rgba(0,0,0,0)',
       strokeColor: 'rgba(0,0,0,0)'
     },
     chosen: {
      edge: (values, id, selected, hovering) => {
        values.width = 2;
      },
      label: (values, id, selected, hovering) => {
        // make label visible on edge click
        values.color = 'black';
        values.strokeColor = 'white';
      },
    }
   }
 }

}
