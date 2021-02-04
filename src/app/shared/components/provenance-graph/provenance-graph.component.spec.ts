import { async, ComponentFixture, TestBed, fakeAsync, tick } from '@angular/core/testing';
import { ElementRef } from '@angular/core';
import { HttpClientModule } from '@angular/common/http';
import { Spectator, createComponentFactory } from '@ngneat/spectator';
import { ProvenanceGraphComponent } from './provenance-graph.component';
import { HomeService } from 'src/app/shared/services/home.service';
import { of } from 'rxjs';
import { delay } from 'rxjs/operators';
import { NgxSpinnerModule } from 'ngx-spinner';
import { HomepageNode } from 'src/app/shared/models/provenance-graph/homepage-node';
import { QueryMatch, Process } from 'src/app/shared/models/QueryBuilder';
const denseGraphData = require('src/app/shared/test/dense-graph-test.json');
const regularGraphData = require('src/app/shared/test/types_graph.json');
const smallGraphData = require('src/app/shared/test/small-graph-test.json');
const multiParentGraphData = require('src/app/shared/test/multi-parent-node-graph.json');
const multiParentClusterData = require('src/app/shared/test/multi-parent-cluster-graph.json');

describe('ProvenanceGraphComponent', () => {
  let spectator: Spectator<ProvenanceGraphComponent>;

  const mockHomeService = {
    getProvenanceGraphSub: () => of(denseGraphData).pipe(delay(0)),
    getProvenanceLoadingSub: () => of(false)
  }

  const createComponent = createComponentFactory({
    component: ProvenanceGraphComponent,
    providers: [
      {
        provide: HomeService,
        useValue: mockHomeService
      }
    ],
    imports: [
      HttpClientModule,
      NgxSpinnerModule
    ],
  })

  beforeEach(() => spectator = createComponent());

  afterEach(() => {
    if (spectator.component.network) {
      spectator.component.network.destroy();
      delete spectator.component.nodes;
      delete spectator.component.edges;
    }
  })

  it('should create', () => {
    expect(spectator.component).toBeTruthy();
  });

  xit('should render graph when data is received', fakeAsync(() => {
    spectator.detectChanges();
    const homeService = spectator.get(HomeService)
    spyOn(spectator.component, 'initNetworkGraph').and.callThrough();
    tick();
    spectator.detectChanges();
    tick();
    spectator.detectChanges();
    expect(spectator.component.initNetworkGraph).toHaveBeenCalled();
  }));

  it('should keep large graphs at a 1:1 ratio', () => {
    spectator.component.canvasWidth = 825;
    spectator.component.canvasHeight = 825;
    const { nodes, edges } = denseGraphData.results;
    spectator.component.calculateScale(nodes, edges);
    expect(spectator.component.xScale).toBe(1);
    expect(spectator.component.yScale).toBe(1);
  });

  it('should scale medium sized graphs to be smaller', () => {
    const { nodes, edges } = regularGraphData.results;
    spectator.component.calculateScale(nodes, edges);
    expect(spectator.component.xScale).toBeLessThan(2);
    expect(spectator.component.yScale).toBeLessThan(2);
  });

  it('should have 1:2 ratio for graphs smaller than viewport', () => {
    const { nodes, edges } = smallGraphData.results;
    spectator.component.calculateScale(nodes, edges);
    expect(spectator.component.xScale).toBe(2);
    expect(spectator.component.yScale).toBe(1);
  });

  it('should emit 1 parent and 1 child for simple search queries', () => {
    spyOn(spectator.component, 'getInputProcesses').and.callThrough();
    spyOn(spectator.component.querySelected, 'emit');
    
    spectator.component.initNetworkGraph(regularGraphData.results);
    spectator.detectChanges();
    spectator.component.submitSearchQuery([15]);

    expect(spectator.component.getInputProcesses).toHaveBeenCalled();
    expect(spectator.component.querySelected.emit).toHaveBeenCalledWith({
      query: new QueryMatch({category: 'DDT_', dataType: 'dynamicCaseDataType', dataModel: 'dynamicCaseDataModel'}),
      process: new Process(['SDT_staticCaseDataType'], ['DDT_dynamicCaseDataType'])
    });
  });

  it('should not try to get process inputs from static types when searching', () => {
    spyOn(spectator.component, 'getInputProcesses');
    spyOn(spectator.component.querySelected, 'emit');

    spectator.component.initNetworkGraph(regularGraphData.results);
    spectator.detectChanges();
    spectator.component.submitSearchQuery([3]);

    expect(spectator.component.getInputProcesses).not.toHaveBeenCalled();
    expect(spectator.component.querySelected.emit).toHaveBeenCalledWith({
      query: new QueryMatch({category: 'SDT_', dataType: 'staticCaseDataType', dataModel: 'staticCaseDataModel'})
    });
  });

  it('should should call getConnectorParents to handle parent processes of connector nodes', () => {
    spyOn(spectator.component, 'getConnectorParents').and.callThrough();
    spyOn(spectator.component.querySelected, 'emit');

    spectator.component.initNetworkGraph(multiParentGraphData.results);
    spectator.detectChanges();
    spectator.component.submitSearchQuery([6]);

    expect(spectator.component.getConnectorParents).toHaveBeenCalled();
    expect(spectator.component.querySelected.emit).toHaveBeenCalledWith({
      query: new QueryMatch({category: 'DDT_', dataType: 'Output2', dataModel: "Output2"}),
      process: new Process(
        ['SDT_Input1', 'SDT_Input2'],
        ['DDT_Output1', 'DDT_Output2']
      )
    });
  });

  it('should search by grandparent node or cluster for clustered nodes', () => {
    /* nodes that are clustered together have an artifical node that is only
    valid in UI. Therefore, we need to get the nodes grandparent. Node Grandparent
    can either be a single node or another connector node */
    spyOn(spectator.component, 'getConnectorParents').and.callThrough();
    spyOn(spectator.component.querySelected, 'emit');

    spectator.component.initNetworkGraph(multiParentClusterData.results);
    spectator.detectChanges();
    spectator.component.submitSearchQuery([6]);

    expect(spectator.component.getConnectorParents).toHaveBeenCalled();
    expect(spectator.component.querySelected.emit).toHaveBeenCalledWith({
      query: new QueryMatch({category: 'DDT_', dataType: 'Output2', dataModel: "Output2"}),
      process: new Process(
        ['SDT_Input1', 'SDT_Input2'],
        ['DDT_Output2']
      )
    });
  });

  it('should render root nodes properly', () => {
    spectator.component.initNetworkGraph(regularGraphData.results);
    spectator.detectChanges();
    const rootData = regularGraphData.results.nodes.find(node => node.root);
    const root = spectator.component.nodes.get(rootData.index) as any;

    expect(root.color).toEqual({
      border: 'darkgreen',
      hover: { background: '#ddd' },
      background: 'white'
    });

    expect(root.margin).toEqual({
      top: 10,
      left: 10,
      bottom: 10,
      right: 10
    });
  });

  it('should render static nodes properly', () => {
    spectator.component.initNetworkGraph(regularGraphData.results);
    spectator.detectChanges();
    const staticData = regularGraphData.results.nodes.find(node => node.category === 'SDT_' && !node.root);
    const staticNode = spectator.component.nodes.get(staticData.index) as any;

    expect(staticNode.color.background).toBe('white');
    expect(staticNode.color.border).toBe('rgb(78, 111, 182)');
    expect(staticNode.shapeProperties.borderRadius).toBe(20);
    expect(staticNode.label).not.toBeUndefined();
  });

  it('should render dynamic nodes properly', () => {
    spectator.component.initNetworkGraph(regularGraphData.results);
    spectator.detectChanges();
    const dynamicData = regularGraphData.results.nodes.find(node => node.category === 'DDT_');
    const dynamicNode = spectator.component.nodes.get(dynamicData.index) as any;

    expect(dynamicNode.color.background).toBe('white');
    expect(dynamicNode.color.border).toBe('rgb(246, 139, 98)');
    expect(dynamicNode.shapeProperties.borderRadius).toBe(0);
    expect(dynamicNode.label).not.toBeUndefined();
  });

  it('should render connector nodes without any shapes or text', () => {
    spectator.component.initNetworkGraph(regularGraphData.results);
    spectator.detectChanges();
    const connectorData = regularGraphData.results.nodes.find(node => node.category === false);
    const connectorNode = spectator.component.nodes.get(connectorData.index) as any;

    expect(connectorNode.color.background).toBe('rgba(0,0,0,0)');
    expect(connectorNode.label).toBeUndefined();
  });

});
