import { async, ComponentFixture, TestBed, fakeAsync, tick } from '@angular/core/testing';
import { ElementRef } from '@angular/core';
import { HttpClientModule } from '@angular/common/http';
import { Spectator, createComponentFactory } from '@ngneat/spectator';
import { ProvenanceGraphComponent } from './provenance-graph.component';
import { HomeService } from 'src/app/shared/services/home.service';
import { of } from 'rxjs';
import { delay } from 'rxjs/operators';
import { NgxSpinnerModule } from 'ngx-spinner';
const mockData = require('src/app/shared/test/mock-provenance-graph.json');
const denseGraphData = require('src/app/shared/test/dense-graph-test.json');
const regularGraphData = require('src/app/shared/test/types_graph.json');
const smallGraphData = require('src/app/shared/test/small-graph-test.json');

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
    expect(spectator.component.xScale).toBeLessThan(1);
    expect(spectator.component.yScale).toBeLessThan(1);
  });

  it('should have 1:2 ratio for graphs smaller than viewport', () => {
    const { nodes, edges } = smallGraphData.results;
    spectator.component.calculateScale(nodes, edges);
    expect(spectator.component.xScale).toBe(2);
    expect(spectator.component.yScale).toBe(1);
  });
});
