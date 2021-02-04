import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { CoreAxisOptionsComponent } from './core-axis-options.component';

describe('CoreAxisOptionsComponent', () => {
  let component: CoreAxisOptionsComponent;
  let fixture: ComponentFixture<CoreAxisOptionsComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ CoreAxisOptionsComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(CoreAxisOptionsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
