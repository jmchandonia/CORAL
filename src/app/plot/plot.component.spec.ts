import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { RouterModule } from '@angular/router';
import { PlotComponent } from './plot.component';
import { Spectator, createComponentFactory } from '@ngneat/spectator';

describe('PlotComponent', () => {
  // let component: PlotComponent;
  // let fixture: ComponentFixture<PlotComponent>;

  // beforeEach(async(() => {
  //   TestBed.configureTestingModule({
  //     declarations: [ PlotComponent ]
  //   })
  //   .compileComponents();
  // }));

  // beforeEach(() => {
  //   fixture = TestBed.createComponent(PlotComponent);
  //   component = fixture.componentInstance;
  //   fixture.detectChanges();
  // });

  let spectator: Spectator<PlotComponent>;
  const createComponent = createComponentFactory({
    component: PlotComponent,
    imports: [
      RouterModule.forRoot([])
    ]
  });

  beforeEach(() => spectator = createComponent());

  it('should create', () => {
    expect(spectator.component).toBeTruthy();
  });
});
