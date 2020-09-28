import { async, ComponentFixture, TestBed, fakeAsync, tick } from '@angular/core/testing';
import { ElementRef } from '@angular/core';
import { HttpClientModule } from '@angular/common/http';
import { Spectator, createComponentFactory } from '@ngneat/spectator';
import { ProvenanceGraphComponent } from './provenance-graph.component';
import { HomeService } from 'src/app/shared/services/home.service';
import { of } from 'rxjs';
import { delay } from 'rxjs/operators';
import { NgxSpinnerModule } from 'ngx-spinner';
import { QueryMatch, Process } from 'src/app/shared/models/QueryBuilder';
const mockData = require('src/app/shared/test/mock-provenance-graph.json');
const denseGraphData = require('src/app/shared/test/dense-graph-test.json');
const regularGraphData = require('src/app/shared/test/types_graph.json');
const smallGraphData = require('src/app/shared/test/small-graph-test.json');
const multiParentGraphData = require('src/app/shared/test/multi-parent-node-graph.json');
const multiParentClusterData = require('src/app/shared/test/multi-parent-cluster-graph.json');

fdescribe('ProvenanceGraphComponent', () => {
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
      query: new QueryMatch({category: 'DDT_', dataType: 'Microbial Sequence', dataModel: 'Brick'}),
      process: new Process(['SDT_Strain'], ['DDT_Microbial Sequence'])
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
      query: new QueryMatch({category: 'SDT_', dataType: 'Strain', dataModel: 'Strain'})
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
      query: new QueryMatch({category: 'DDT_', dataType: 'Microbial Abundance', dataModel: "Brick"}),
      process: new Process(
        ['SDT_Well', 'SDT_Image'],
        ['DDT_Chemical Measurement', 'DDT_Microbial Abundance']
      )
    });
  });

  it('should search by grandparent node or cluster for clustered nodes', () => {
    spyOn(spectator.component, 'getConnectorParents').and.callThrough();
    spyOn(spectator.component.querySelected, 'emit');

    spectator.component.initNetworkGraph(multiParentClusterData.results);
    spectator.detectChanges();
    spectator.component.submitSearchQuery([6]);

    expect(spectator.component.getConnectorParents).toHaveBeenCalled();
    expect(spectator.component.querySelected.emit).toHaveBeenCalledWith({
      query: new QueryMatch({category: 'DDT_', dataType: 'Microbial Abundance', dataModel: "Brick"}),
      process: new Process(
        ['SDT_Well', 'SDT_Image'],
        ['DDT_Microbial Abundance']
      )
    });
  });
});
