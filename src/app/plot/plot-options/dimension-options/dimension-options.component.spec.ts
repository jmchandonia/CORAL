import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { DimensionOptionsComponent } from './dimension-options.component';

describe('DimensionOptionsComponent', () => {
  let component: DimensionOptionsComponent;
  let fixture: ComponentFixture<DimensionOptionsComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ DimensionOptionsComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(DimensionOptionsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
