import { async, ComponentFixture, TestBed, fakeAsync, tick } from '@angular/core/testing';
import { HttpClientModule } from '@angular/common/http';
import { Spectator, createComponentFactory } from '@ngneat/spectator';
import { ProvenanceGraphComponent } from './provenance-graph.component';
import { HomeService } from 'src/app/shared/services/home.service';
import { of } from 'rxjs';
import { delay } from 'rxjs/operators';
import { NgxSpinnerModule } from 'ngx-spinner';
const mockData = require('src/app/shared/test/mock-provenance-graph.json');

xdescribe('ProvenanceGraphComponent', () => {
  // let component: ProvenanceGraphComponent;
  // let fixture: ComponentFixture<ProvenanceGraphComponent>;

  // beforeEach(async(() => {
  //   TestBed.configureTestingModule({
  //     declarations: [ ProvenanceGraphComponent ]
  //   })
  //   .compileComponents();
  // }));

  // beforeEach(() => {
  //   fixture = TestBed.createComponent(ProvenanceGraphComponent);
  //   component = fixture.componentInstance;
  //   fixture.detectChanges();
  // });

  let spectator: Spectator<ProvenanceGraphComponent>;

  const mockHomeService = {
    getProvenanceGraphSub: () => of(mockData).pipe(delay(3000)),
    getProvenanceLoadingSub: () => of(true)
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
    ]
  })

  beforeEach(() => spectator = createComponent());

  it('should create', () => {
    expect(spectator.component).toBeTruthy();
  });

  it('should render graph when data is received', fakeAsync(() => {
    spectator.detectChanges();
    const homeService = spectator.get(HomeService)
    // spyOn(homeService, 'getProvenanceGraphSub').and.callThrough();
    spyOn(spectator.component, 'initNetworkGraph').and.callThrough();
    tick();
    spectator.detectChanges();
    expect(spectator.component.initNetworkGraph).toHaveBeenCalled();
    // expect(homeService.getProvenanceGraphSub).toHaveBeenCalled();
  }));
});
