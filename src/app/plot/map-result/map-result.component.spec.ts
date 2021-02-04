import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { MapResultComponent } from './map-result.component';

describe('MapResultComponent', () => {
  let component: MapResultComponent;
  let fixture: ComponentFixture<MapResultComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ MapResultComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(MapResultComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
