import { Component, OnInit, ElementRef, ViewChild, AfterViewInit, EventEmitter, Output } from '@angular/core';
import { Network, DataSet, Node, Edge, NodeChosen } from 'vis-network/standalone';
const mockData = require('src/app/shared/test/mock-provenance-graph.json');
const mockData_v2 = require('src/app/shared/test/mock-provenance-graph_v2.json');
import { QueryMatch } from 'src/app/shared/models/QueryBuilder';
import { partition } from 'lodash';
import { HomeService } from 'src/app/shared/services/home.service';

@Component({
  selector: 'app-provenance-graph',
  templateUrl: './provenance-graph.component.html',
  styleUrls: ['./provenance-graph.component.css']
})
export class ProvenanceGraphComponent implements OnInit, AfterViewInit {

  nodes:  DataSet<any>;
  edges: DataSet<any>;
  clusterNodes: any[] = []; // TODO: make models for response JSON
  @Output() querySelected: EventEmitter<QueryMatch> = new EventEmitter();

  @ViewChild('pGraph') pGraph: ElementRef;

  options = {
    interaction: {
      zoomView: false,
      dragView: false,
      hover: true
    },
    physics: {
      barnesHut: {
        springConstant: 0.1,
        avoidOverlap: 10
      },
    },
    layout: {
      randomSeed: '0:0',
    },
  };

  coreTypeNodes: any[];
  dynamicTypeNodes: any[];

  network: Network;

  constructor(
    private homeService: HomeService
  ) { }

  ngOnInit(): void {
    this.homeService.getProvenanceGraphData()
      .subscribe(data => {
        let temporaryResponseFix = data
          .replace(/\'/g, '"')
          .replace(/\n/g, ' ')
          .replace(/True/g, 'true')
          .replace(/False/g, 'false');
        this.initNetworkGraph(JSON.parse(temporaryResponseFix));
      });
  }

  initNetworkGraph(data) {
    console.log('DATA', data);
    const [coreTypes, dynamicTypes] = partition(data.nodes, node => node.category !== 'DDT_');

    // initialize core type nodes with x y coordinates
    this.nodes = new DataSet(coreTypes.map(this.createNode));

    // layout dynamic types with visJS physics engine
    dynamicTypes.forEach(dynamicType => {
      if (dynamicType.children?.length) {
        // add node children to nodeList
        dynamicType.children.forEach(child => {
          this.nodes.update(this.createNode(child));
        });
        // add node to list of nodes that need to be clustered
        this.clusterNodes.push({...dynamicType, expanded: true});
      }
      this.nodes.update(this.createNode(dynamicType));
    });

    // initialize edges
    this.edges = new DataSet(
      data.links.map(edge => this.createEdge(edge))
    );

    // render network
    this.network = new Network(
      this.pGraph.nativeElement,
      {
        nodes: this.nodes,
        edges: this.edges
      },
      this.options
    );

    // cluster nodes from clusterNodes array
    this.clusterNodes.forEach(clusterNode => this.addCluster(clusterNode));

    // set zoom level to contain all nodes
    this.network.fit({
      nodes: this.nodes.map(node => node.id),
      animation: false
    });

    // add double click event listener to submit search query on nodes
    this.network.on('doubleClick', ({nodes}) => this.submitSearchQuery(nodes));

    // add click event to expand cluster nodes
    this.network.on('click', ({nodes}) => {
      const clusteredNode = this.clusterNodes.find(node => node.index === nodes[0]);
      if(clusteredNode && clusteredNode.expanded) {
        this.reclusterNode(nodes[0]);
      }
    });

    // disable physics after nodes without coordinates have been pushed apart
    this.network.on('stabilizationIterationsDone', () => this.network.setOptions({physics: false}));
  }

  ngAfterViewInit(): void {
 }

 addCluster(data) {
   // configuration for nodes that hold clusters together
   this.network.cluster({
    joinCondition: node => (node.cid && node.cid === data.index) || node.id === data.index,
    clusterNodeProperties: {
      label: `${data.count} ${data.name} [+]`,
      physics: false,
      color: {
        border: data.category === 'DDT_' ? 'rgb(246, 139, 98)' : 'rgb(78, 111, 182)',
        background: 'white'
      },
      shape: 'box',
      x: data.x,
      y: data.y,
      font: {
        size: 16,
        face: 'Red Hat Text, sans-serif'
      },
      chosen: {
        node: (values, id, selected, hovering) => {
          if (selected) {
            data.expanded = true;
            this.network.openCluster(id, {
              // function to move child nodes to their specified position
              releaseFunction: (_, positions) => positions 
            })
          }
        },
        label: (values, id, selected) => {
          if(selected) { values.size = 0; }
        }
      } as NodeChosen
    },
   });
 }

 reclusterNode(nodeID) {
   const cluster = this.clusterNodes.find(item => item.index === nodeID);
   this.addCluster(cluster);
 }

  createNode(dataItem: any): Node {
    const node: any = {
      id: dataItem.index,
      label: dataItem.category !== false && !dataItem.children ? `${dataItem.count} ${dataItem.name}` : '',
      font: {
        size: 16,
        face: 'Red Hat Text, sans-serif'
      },
      color: {
        background: dataItem.category !== false ? 'white' : 'rgba(0,0,0,0)',
        border: dataItem.category === 'DDT_' ? 'rgb(246, 139, 98)' : 'rgb(78, 111, 182)',
        hover: { background: '#ddd' }
      },
      borderWidth: dataItem.category === false ? 0 : 1,
      physics: true,
      cid: dataItem.cid,
      shape: 'box',
      shapeProperties: {
        borderRadius: dataItem.category === 'DDT_' ? 0 : 20
      },
      data: {...dataItem},
      fixed: dataItem.category !== 'DDT_',
    }

    // if(typeof dataItem.x === 'number' && typeof dataItem.y === 'number') {
    //   node.x = dataItem.x;
    //   node.y = dataItem.y;
    // }

    if(typeof dataItem.x_rank === 'number') {
      node.x = dataItem.x_rank * 150;
    }

    if (typeof dataItem.y_rank === 'number' && dataItem.category === 'SDT_') {
      node.y = dataItem.y_rank * 100;
    }

    if(dataItem.category === 'SDT_') { node.mass = 10; }

    return node;
  }

  createEdge(edge): any {
    const toId = edge.target;
    const fromId = edge.source;
    const target: any = this.nodes.get(toId);
    return {
      from: fromId,
      to: toId,
      width: edge.thickness,
      label: edge.hoverText.replace(/<br>/g, '\n').replace(/&rarr;/g, ' → '), // TODO: implement safeHtmlParser
      color: '#777',
      physics: true,
      selfReference: {
        angle: 0.22
      },
      font: {
        // hide labels initially
        size: 16,
        color: 'rgba(0,0,0,0)',
        strokeColor: 'rgba(0,0,0,0)'
      },
      arrows: {
        to: {
          // hide arrows for 'connector' nodes
          enabled: target && target.data.category !== 'null'
        }
      },
      smooth: {
        enabled: (fromId === 13 || toId === 13),
        roundness: 0.2,
        forceDirection: 'vertical',
        type: 'curvedCW'
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

  submitSearchQuery(nodes) {
    if (nodes.length) {
      const { category, dataType, dataModel } = this.nodes.get(nodes)[0].data;
      const query = new QueryMatch({category, dataType, dataModel});
      this.querySelected.emit(query);
    }
  }

}
